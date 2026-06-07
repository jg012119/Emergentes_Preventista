"""
Script de entrenamiento para el modelo aje-preventista via Ollama Modelfile.

Genera un modelo personalizado con:
  1. System prompt alineado con el schema LlamaIntent Pydantic actual
  2. 40+ ejemplos few-shot de español boliviano coloquial baked-in
  3. Evaluación por épocas con métricas de intención, producto, presentación y cantidad
  4. El mejor modelo se exporta como 'aje-preventista'

Run desde backend/:
    python -m scratch.train_llm_model

Prerequisites:
    ollama serve
    ollama pull llama3.1:8b
"""

import asyncio
import json
import os
import subprocess
import sys
import time
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm import ask_llm, check_ollama_status, build_catalog_text
from app.models.schemas import LlamaIntent

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
DATASET_PATH = Path(__file__).parent.parent / "app" / "nlp_dataset" / "cochabamba_cercado_orders.json"
BASE_MODEL   = "llama3.1:8b"
OUTPUT_MODEL = "aje-preventista"
EPOCHS       = 2
EVAL_SAMPLE  = 30   # evaluados por época

MOCK_PRODUCTS = [
    {"id": "1",  "name": "Big Cola 3L",      "price": 12.00, "stock": 200},
    {"id": "2",  "name": "Big Cola 2L",      "price":  9.00, "stock": 300},
    {"id": "3",  "name": "Big Cola 1L",      "price":  6.00, "stock": 400},
    {"id": "4",  "name": "Big Cola 500ml",   "price":  4.00, "stock": 500},
    {"id": "5",  "name": "Coca-Cola 2L",     "price": 14.00, "stock": 150},
    {"id": "6",  "name": "Coca-Cola 1L",     "price": 10.00, "stock": 250},
    {"id": "7",  "name": "Coca-Cola 500ml",  "price":  7.00, "stock": 350},
    {"id": "8",  "name": "Sporade 500ml",    "price":  8.00, "stock": 300},
    {"id": "9",  "name": "Sporade 1L",       "price": 12.00, "stock": 200},
    {"id": "10", "name": "Cifrut 500ml",     "price":  5.00, "stock": 400},
    {"id": "11", "name": "Cifrut 1L",        "price":  8.00, "stock": 250},
    {"id": "12", "name": "Cifrut 2L",        "price": 12.00, "stock": 150},
    {"id": "13", "name": "Volt 300ml",       "price":  8.00, "stock": 200},
    {"id": "14", "name": "Volt 500ml",       "price": 12.00, "stock": 150},
    {"id": "15", "name": "Agua Cielo 500ml", "price":  3.00, "stock": 600},
    {"id": "16", "name": "Agua Cielo 1L",    "price":  5.00, "stock": 400},
    {"id": "17", "name": "Agua Cielo 2.5L",  "price":  8.00, "stock": 200},
    {"id": "18", "name": "Pulp 300ml",       "price":  5.00, "stock": 300},
    {"id": "19", "name": "Pulp 1L",          "price":  9.00, "stock": 200},
    {"id": "20", "name": "Oro 500ml",        "price":  4.50, "stock": 300},
    {"id": "21", "name": "Oro 2L",           "price":  8.50, "stock": 220},
    {"id": "22", "name": "Free Tea 500ml",   "price":  6.00, "stock": 250},
]

# ---------------------------------------------------------------------------
# Sistema de colores
# ---------------------------------------------------------------------------
def color(text, code): return f"\033[{code}m{text}\033[0m"
GREEN, RED, YELLOW, CYAN, MAGENTA, BOLD = 32, 31, 33, 36, 35, 1

# ---------------------------------------------------------------------------
# Ejemplos few-shot baked-in — 42 ejemplos con el schema LlamaIntent actual
# ---------------------------------------------------------------------------
FEW_SHOT_CONVERSATIONS = [
    # ── PEDIDOS SIMPLES ──────────────────────────────────────────
    {
        "user": "manda 2 coquitas de 3 litros",
        "assistant": json.dumps({
            "intencion": "pedido", "confianza": 0.97, "motivo_rechazo": None,
            "productos": [{"texto_original": "coquitas de 3 litros", "nombre_detectado": "Coca-Cola", "cantidad": 2, "presentacion": "3L", "sku_sugerido": "Coca-Cola 2L", "requiere_aclaracion": False}],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None, "mensaje_libre": None
        }, ensure_ascii=False),
    },
    {
        "user": "dame 3 big cola familiares",
        "assistant": json.dumps({
            "intencion": "pedido", "confianza": 0.99, "motivo_rechazo": None,
            "productos": [{"texto_original": "big cola familiares", "nombre_detectado": "Big Cola", "cantidad": 3, "presentacion": "2L", "sku_sugerido": "Big Cola 2L", "requiere_aclaracion": False}],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None, "mensaje_libre": None
        }, ensure_ascii=False),
    },
    {
        "user": "quiero una agüita cielo chica",
        "assistant": json.dumps({
            "intencion": "pedido", "confianza": 0.99, "motivo_rechazo": None,
            "productos": [{"texto_original": "agüita cielo chica", "nombre_detectado": "Agua Cielo", "cantidad": 1, "presentacion": "500ml", "sku_sugerido": "Agua Cielo 500ml", "requiere_aclaracion": False}],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None, "mensaje_libre": None
        }, ensure_ascii=False),
    },
    {
        "user": "dame 4 cielitos",
        "assistant": json.dumps({
            "intencion": "pedido", "confianza": 0.98, "motivo_rechazo": None,
            "productos": [{"texto_original": "cielitos", "nombre_detectado": "Agua Cielo", "cantidad": 4, "presentacion": "500ml", "sku_sugerido": "Agua Cielo 500ml", "requiere_aclaracion": False}],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None, "mensaje_libre": None
        }, ensure_ascii=False),
    },
    {
        "user": "pasame dos voltcitos",
        "assistant": json.dumps({
            "intencion": "pedido", "confianza": 0.98, "motivo_rechazo": None,
            "productos": [{"texto_original": "voltcitos", "nombre_detectado": "Volt", "cantidad": 2, "presentacion": "300ml", "sku_sugerido": "Volt 300ml", "requiere_aclaracion": False}],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None, "mensaje_libre": None
        }, ensure_ascii=False),
    },
    {
        "user": "agrega 5 oritos y 3 pulpitos",
        "assistant": json.dumps({
            "intencion": "pedido", "confianza": 0.97, "motivo_rechazo": None,
            "productos": [
                {"texto_original": "oritos", "nombre_detectado": "Oro", "cantidad": 5, "presentacion": "500ml", "sku_sugerido": "Oro 500ml", "requiere_aclaracion": False},
                {"texto_original": "pulpitos", "nombre_detectado": "Pulp", "cantidad": 3, "presentacion": "300ml", "sku_sugerido": "Pulp 300ml", "requiere_aclaracion": False},
            ],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None, "mensaje_libre": None
        }, ensure_ascii=False),
    },
    # ── PEDIDOS CON PRESENTACIÓN EXPLÍCITA ──────────────────────
    {
        "user": "dame 6 big cola de 2 litros y 4 cielo litro",
        "assistant": json.dumps({
            "intencion": "pedido", "confianza": 0.99, "motivo_rechazo": None,
            "productos": [
                {"texto_original": "big cola de 2 litros", "nombre_detectado": "Big Cola", "cantidad": 6, "presentacion": "2L", "sku_sugerido": "Big Cola 2L", "requiere_aclaracion": False},
                {"texto_original": "cielo litro", "nombre_detectado": "Agua Cielo", "cantidad": 4, "presentacion": "1L", "sku_sugerido": "Agua Cielo 1L", "requiere_aclaracion": False},
            ],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None, "mensaje_libre": None
        }, ensure_ascii=False),
    },
    {
        "user": "necesito 2 volt 500 y una big de 3",
        "assistant": json.dumps({
            "intencion": "pedido", "confianza": 0.96, "motivo_rechazo": None,
            "productos": [
                {"texto_original": "volt 500", "nombre_detectado": "Volt", "cantidad": 2, "presentacion": "500ml", "sku_sugerido": "Volt 500ml", "requiere_aclaracion": False},
                {"texto_original": "big de 3", "nombre_detectado": "Big Cola", "cantidad": 1, "presentacion": "3L", "sku_sugerido": "Big Cola 3L", "requiere_aclaracion": False},
            ],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None, "mensaje_libre": None
        }, ensure_ascii=False),
    },
    {
        "user": "quiero 10 agua de 500 ml",
        "assistant": json.dumps({
            "intencion": "pedido", "confianza": 0.97, "motivo_rechazo": None,
            "productos": [{"texto_original": "agua de 500 ml", "nombre_detectado": "Agua Cielo", "cantidad": 10, "presentacion": "500ml", "sku_sugerido": "Agua Cielo 500ml", "requiere_aclaracion": False}],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None, "mensaje_libre": None
        }, ensure_ascii=False),
    },
    # ── PEDIDOS CON FECHA ────────────────────────────────────────
    {
        "user": "mándame 5 cielo chica para mañana",
        "assistant": json.dumps({
            "intencion": "pedido", "confianza": 0.97, "motivo_rechazo": None,
            "productos": [{"texto_original": "cielo chica", "nombre_detectado": "Agua Cielo", "cantidad": 5, "presentacion": "500ml", "sku_sugerido": "Agua Cielo 500ml", "requiere_aclaracion": False}],
            "fecha_entrega": "tomorrow", "requiere_aclaracion": False, "pregunta_aclaracion": None, "mensaje_libre": None
        }, ensure_ascii=False),
    },
    {
        "user": "3 big familiares pa el viernes",
        "assistant": json.dumps({
            "intencion": "pedido", "confianza": 0.96, "motivo_rechazo": None,
            "productos": [{"texto_original": "big familiares", "nombre_detectado": "Big Cola", "cantidad": 3, "presentacion": "2L", "sku_sugerido": "Big Cola 2L", "requiere_aclaracion": False}],
            "fecha_entrega": "friday", "requiere_aclaracion": False, "pregunta_aclaracion": None, "mensaje_libre": None
        }, ensure_ascii=False),
    },
    # ── PEDIDOS MULTI-PRODUCTO ───────────────────────────────────
    {
        "user": "dame 3 volts 500 y 2 big cola y una cifrut",
        "assistant": json.dumps({
            "intencion": "pedido", "confianza": 0.97, "motivo_rechazo": None,
            "productos": [
                {"texto_original": "volts 500", "nombre_detectado": "Volt", "cantidad": 3, "presentacion": "500ml", "sku_sugerido": "Volt 500ml", "requiere_aclaracion": False},
                {"texto_original": "big cola", "nombre_detectado": "Big Cola", "cantidad": 2, "presentacion": None, "sku_sugerido": None, "requiere_aclaracion": True},
                {"texto_original": "cifrut", "nombre_detectado": "Cifrut", "cantidad": 1, "presentacion": None, "sku_sugerido": None, "requiere_aclaracion": True},
            ],
            "fecha_entrega": None, "requiere_aclaracion": True, "pregunta_aclaracion": "¿Qué presentación de Big Cola y Cifrut quieres?", "mensaje_libre": None
        }, ensure_ascii=False),
    },
    {
        "user": "necesito una docena de cielo chica y 6 volt lata",
        "assistant": json.dumps({
            "intencion": "pedido", "confianza": 0.98, "motivo_rechazo": None,
            "productos": [
                {"texto_original": "docena de cielo chica", "nombre_detectado": "Agua Cielo", "cantidad": 12, "presentacion": "500ml", "sku_sugerido": "Agua Cielo 500ml", "requiere_aclaracion": False},
                {"texto_original": "volt lata", "nombre_detectado": "Volt", "cantidad": 6, "presentacion": "300ml", "sku_sugerido": "Volt 300ml", "requiere_aclaracion": False},
            ],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None, "mensaje_libre": None
        }, ensure_ascii=False),
    },
    # ── PEDIDOS CON TYPOS ────────────────────────────────────────
    {
        "user": "sielo grande x2 y votl lata x3",
        "assistant": json.dumps({
            "intencion": "pedido", "confianza": 0.93, "motivo_rechazo": None,
            "productos": [
                {"texto_original": "sielo grande", "nombre_detectado": "Agua Cielo", "cantidad": 2, "presentacion": "2.5L", "sku_sugerido": "Agua Cielo 2.5L", "requiere_aclaracion": False},
                {"texto_original": "votl lata", "nombre_detectado": "Volt", "cantidad": 3, "presentacion": "300ml", "sku_sugerido": "Volt 300ml", "requiere_aclaracion": False},
            ],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None, "mensaje_libre": None
        }, ensure_ascii=False),
    },
    {
        "user": "bigg cola 2 litros por favor",
        "assistant": json.dumps({
            "intencion": "pedido", "confianza": 0.94, "motivo_rechazo": None,
            "productos": [{"texto_original": "bigg cola 2 litros", "nombre_detectado": "Big Cola", "cantidad": 1, "presentacion": "2L", "sku_sugerido": "Big Cola 2L", "requiere_aclaracion": False}],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None, "mensaje_libre": None
        }, ensure_ascii=False),
    },
    {
        "user": "cifru 500 y un cifrutcito",
        "assistant": json.dumps({
            "intencion": "pedido", "confianza": 0.93, "motivo_rechazo": None,
            "productos": [
                {"texto_original": "cifru 500", "nombre_detectado": "Cifrut", "cantidad": 1, "presentacion": "500ml", "sku_sugerido": "Cifrut 500ml", "requiere_aclaracion": False},
                {"texto_original": "cifrutcito", "nombre_detectado": "Cifrut", "cantidad": 1, "presentacion": "500ml", "sku_sugerido": "Cifrut 500ml", "requiere_aclaracion": False},
            ],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None, "mensaje_libre": None
        }, ensure_ascii=False),
    },
    # ── AMBIGUOS — REQUIEREN ACLARACIÓN ─────────────────────────
    {
        "user": "quiero 3 big cola",
        "assistant": json.dumps({
            "intencion": "pedido", "confianza": 0.88, "motivo_rechazo": None,
            "productos": [{"texto_original": "big cola", "nombre_detectado": "Big Cola", "cantidad": 3, "presentacion": None, "sku_sugerido": None, "requiere_aclaracion": True}],
            "fecha_entrega": None, "requiere_aclaracion": True,
            "pregunta_aclaracion": "¿Qué presentación de Big Cola quieres? Tenemos: 500ml, 1L, 2L, 3L",
            "mensaje_libre": None
        }, ensure_ascii=False),
    },
    {
        "user": "dame dos aguas",
        "assistant": json.dumps({
            "intencion": "pedido", "confianza": 0.86, "motivo_rechazo": None,
            "productos": [{"texto_original": "aguas", "nombre_detectado": "Agua Cielo", "cantidad": 2, "presentacion": None, "sku_sugerido": None, "requiere_aclaracion": True}],
            "fecha_entrega": None, "requiere_aclaracion": True,
            "pregunta_aclaracion": "¿Qué tamaño de Agua Cielo quieres? Tenemos: 500ml, 1L, 2.5L",
            "mensaje_libre": None
        }, ensure_ascii=False),
    },
    # ── FUERA DE ALCANCE — ALCOHOL ───────────────────────────────
    {
        "user": "dame una cheba bien fría",
        "assistant": json.dumps({
            "intencion": "fuera_de_alcance", "confianza": 1.0,
            "motivo_rechazo": "alcohol", "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": "❌ Lamento informarte que no distribuimos bebidas alcohólicas."
        }, ensure_ascii=False),
    },
    {
        "user": "manda 6 cervezas",
        "assistant": json.dumps({
            "intencion": "fuera_de_alcance", "confianza": 1.0,
            "motivo_rechazo": "alcohol", "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": "❌ No distribuimos bebidas alcohólicas como la cerveza."
        }, ensure_ascii=False),
    },
    {
        "user": "una birra helada si tienes",
        "assistant": json.dumps({
            "intencion": "fuera_de_alcance", "confianza": 1.0,
            "motivo_rechazo": "alcohol", "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": "❌ No contamos con distribución de bebidas alcohólicas."
        }, ensure_ascii=False),
    },
    {
        "user": "quiero vino y ron para el cumple",
        "assistant": json.dumps({
            "intencion": "fuera_de_alcance", "confianza": 1.0,
            "motivo_rechazo": "alcohol", "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": "❌ No distribuimos bebidas alcohólicas como vino o ron."
        }, ensure_ascii=False),
    },
    # ── FUERA DE ALCANCE — COMIDA SÓLIDA ────────────────────────
    {
        "user": "quiero unas papitas",
        "assistant": json.dumps({
            "intencion": "fuera_de_alcance", "confianza": 1.0,
            "motivo_rechazo": "comida_solida", "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": "❌ Nos especializamos en bebidas. No contamos con comida sólida como papitas."
        }, ensure_ascii=False),
    },
    {
        "user": "papas y chela para el partido",
        "assistant": json.dumps({
            "intencion": "fuera_de_alcance", "confianza": 1.0,
            "motivo_rechazo": "comida_solida", "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": "❌ No distribuimos comida sólida ni bebidas alcohólicas. Solo bebidas AJE."
        }, ensure_ascii=False),
    },
    {
        "user": "tienes nachos o galletas?",
        "assistant": json.dumps({
            "intencion": "fuera_de_alcance", "confianza": 1.0,
            "motivo_rechazo": "comida_solida", "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": "❌ Solo distribuimos bebidas. No contamos con snacks ni comida sólida."
        }, ensure_ascii=False),
    },
    # ── CONSULTAS DE CATÁLOGO ────────────────────────────────────
    {
        "user": "qué tienes para el calor?",
        "assistant": json.dumps({
            "intencion": "consulta_catalogo", "confianza": 0.95,
            "motivo_rechazo": None, "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": "¡Con gusto! Te paso el menú de bebidas disponibles para que elijas."
        }, ensure_ascii=False),
    },
    {
        "user": "muéstrame lo que tienen disponible",
        "assistant": json.dumps({
            "intencion": "consulta_catalogo", "confianza": 0.99,
            "motivo_rechazo": None, "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": "Te paso el menú de bebidas disponibles."
        }, ensure_ascii=False),
    },
    {
        "user": "qué bebidas tienen?",
        "assistant": json.dumps({
            "intencion": "consulta_catalogo", "confianza": 0.98,
            "motivo_rechazo": None, "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": "Aquí tienes el catálogo de bebidas disponibles."
        }, ensure_ascii=False),
    },
    {
        "user": "que tienen de agua?",
        "assistant": json.dumps({
            "intencion": "consulta_catalogo", "confianza": 0.92,
            "motivo_rechazo": None, "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": "Tenemos Agua Cielo en 500ml, 1L y 2.5L. ¿Cuál te enviamos?"
        }, ensure_ascii=False),
    },
    # ── SALUDOS ──────────────────────────────────────────────────
    {
        "user": "hola buenas tardes",
        "assistant": json.dumps({
            "intencion": "saludo", "confianza": 1.0,
            "motivo_rechazo": None, "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": "¡Hola! 😊 Soy tu asistente AJE Bolivia. ¿Qué bebidas te envío hoy?"
        }, ensure_ascii=False),
    },
    {
        "user": "buenas, soy el preventista de zona norte",
        "assistant": json.dumps({
            "intencion": "saludo", "confianza": 0.97,
            "motivo_rechazo": None, "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": "¡Buenas! 👋 ¿Qué pedido armamos hoy?"
        }, ensure_ascii=False),
    },
    {
        "user": "buen dia, gracias",
        "assistant": json.dumps({
            "intencion": "saludo", "confianza": 0.99,
            "motivo_rechazo": None, "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": "¡Buen día! 😊 Con gusto te ayudo. ¿Qué necesitas?"
        }, ensure_ascii=False),
    },
    # ── CONFIRMACIÓN / NEGACIÓN ──────────────────────────────────
    {
        "user": "sí, confirmo",
        "assistant": json.dumps({
            "intencion": "confirmacion", "confianza": 0.99,
            "motivo_rechazo": None, "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": None
        }, ensure_ascii=False),
    },
    {
        "user": "dale, mándalo",
        "assistant": json.dumps({
            "intencion": "confirmacion", "confianza": 0.98,
            "motivo_rechazo": None, "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": None
        }, ensure_ascii=False),
    },
    {
        "user": "no, cancelar",
        "assistant": json.dumps({
            "intencion": "negacion", "confianza": 0.99,
            "motivo_rechazo": None, "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": "Entendido, sin problema. Avisame cuando necesites algo."
        }, ensure_ascii=False),
    },
    # ── LISTAR / ESTADO PEDIDOS ──────────────────────────────────
    {
        "user": "cómo va mi pedido?",
        "assistant": json.dumps({
            "intencion": "estado_pedido", "confianza": 0.97,
            "motivo_rechazo": None, "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": None
        }, ensure_ascii=False),
    },
    {
        "user": "muéstrame mis pedidos pendientes",
        "assistant": json.dumps({
            "intencion": "listar_pedidos", "confianza": 0.98,
            "motivo_rechazo": None, "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": None
        }, ensure_ascii=False),
    },
    # ── ACLARACIÓN ───────────────────────────────────────────────
    {
        "user": "de litro",
        "assistant": json.dumps({
            "intencion": "aclaracion", "confianza": 0.85,
            "motivo_rechazo": None, "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": None
        }, ensure_ascii=False),
    },
    {
        "user": "la de 500",
        "assistant": json.dumps({
            "intencion": "aclaracion", "confianza": 0.84,
            "motivo_rechazo": None, "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": None
        }, ensure_ascii=False),
    },
    {
        "user": "chico",
        "assistant": json.dumps({
            "intencion": "aclaracion", "confianza": 0.88,
            "motivo_rechazo": None, "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": None
        }, ensure_ascii=False),
    },
    {
        "user": "el de dos litros",
        "assistant": json.dumps({
            "intencion": "aclaracion", "confianza": 0.89,
            "motivo_rechazo": None, "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": None
        }, ensure_ascii=False),
    },
    {
        "user": "de tres litros",
        "assistant": json.dumps({
            "intencion": "aclaracion", "confianza": 0.87,
            "motivo_rechazo": None, "productos": [],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None,
            "mensaje_libre": None
        }, ensure_ascii=False),
    },
    # ── TRANSCRIPCIONES DE VOZ (sin puntuación, vacilaciones, coloquiales) ──
    {
        "user": "ehhh quiero free tea de medio litro tres unidades para mañana",
        "assistant": json.dumps({
            "intencion": "pedido", "confianza": 0.97, "motivo_rechazo": None,
            "productos": [{"texto_original": "free tea de medio litro tres unidades", "nombre_detectado": "Free Tea", "cantidad": 3, "presentacion": "500ml", "sku_sugerido": "Free Tea 500ml", "requiere_aclaracion": False}],
            "fecha_entrega": "tomorrow", "requiere_aclaracion": False, "pregunta_aclaracion": None, "mensaje_libre": None
        }, ensure_ascii=False),
    },
    {
        "user": "hola me das cuatro big cola de tres litros para hoy por favor",
        "assistant": json.dumps({
            "intencion": "pedido", "confianza": 0.98, "motivo_rechazo": None,
            "productos": [{"texto_original": "cuatro big cola de tres litros", "nombre_detectado": "Big Cola", "cantidad": 4, "presentacion": "3L", "sku_sugerido": "Big Cola 3L", "requiere_aclaracion": False}],
            "fecha_entrega": "today", "requiere_aclaracion": False, "pregunta_aclaracion": None, "mensaje_libre": None
        }, ensure_ascii=False),
    },
    {
        "user": "bueno entonces dame cuatro big cola de 500 y seis oro chico",
        "assistant": json.dumps({
            "intencion": "pedido", "confianza": 0.96, "motivo_rechazo": None,
            "productos": [
                {"texto_original": "cuatro big cola de 500", "nombre_detectado": "Big Cola", "cantidad": 4, "presentacion": "500ml", "sku_sugerido": "Big Cola 500ml", "requiere_aclaracion": False},
                {"texto_original": "seis oro chico", "nombre_detectado": "Oro", "cantidad": 6, "presentacion": "500ml", "sku_sugerido": "Oro 500ml", "requiere_aclaracion": False}
            ],
            "fecha_entrega": None, "requiere_aclaracion": False, "pregunta_aclaracion": None, "mensaje_libre": None
        }, ensure_ascii=False),
    },
    {
        "user": "a ver ponme dos big de dos y tres cifrut de litro y un volt grande para hoy",
        "assistant": json.dumps({
            "intencion": "pedido", "confianza": 0.95, "motivo_rechazo": None,
            "productos": [
                {"texto_original": "dos big de dos", "nombre_detectado": "Big Cola", "cantidad": 2, "presentacion": "2L", "sku_sugerido": "Big Cola 2L", "requiere_aclaracion": False},
                {"texto_original": "tres cifrut de litro", "nombre_detectado": "Cifrut", "cantidad": 3, "presentacion": "1L", "sku_sugerido": "Cifrut 1L", "requiere_aclaracion": False},
                {"texto_original": "un volt grande", "nombre_detectado": "Volt", "cantidad": 1, "presentacion": "500ml", "sku_sugerido": "Volt 500ml", "requiere_aclaracion": False}
            ],
            "fecha_entrega": "today", "requiere_aclaracion": False, "pregunta_aclaracion": None, "mensaje_libre": None
        }, ensure_ascii=False),
    },
]


def load_dataset():
    """Carga el dataset del disco y lo mezcla con los FEW_SHOT_CONVERSATIONS."""
    try:
        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(color(f"  ⚠️  Dataset no encontrado en {DATASET_PATH}. Usando solo ejemplos internos.", YELLOW))
        raw = []

    # Convert dataset format to conversation format with LlamaIntent schema
    extra = []
    for example in raw:
        text  = example.get("text", "")
        items = example.get("items", [])
        if not text or not items:
            continue

        productos = []
        for item in items:
            product = item.get("product", "")
            if not product:
                continue
            productos.append({
                "texto_original": item.get("raw_text", text),
                "nombre_detectado": product.rsplit(" ", 1)[0] if any(c.isdigit() for c in product[-3:]) else product,
                "cantidad": item.get("quantity", 1),
                "presentacion": item.get("presentation"),
                "sku_sugerido": product,
                "requiere_aclaracion": False,
            })

        if not productos:
            continue

        extra.append({
            "user": text,
            "assistant": json.dumps({
                "intencion": "pedido", "confianza": 0.92, "motivo_rechazo": None,
                "productos": productos,
                "fecha_entrega": example.get("delivery_date"),
                "requiere_aclaracion": False,
                "pregunta_aclaracion": None,
                "mensaje_libre": None,
            }, ensure_ascii=False),
        })

    print(f"  Ejemplos internos  : {len(FEW_SHOT_CONVERSATIONS)}")
    print(f"  Ejemplos del dataset: {len(extra)}")
    all_convs = FEW_SHOT_CONVERSATIONS + extra
    print(f"  Total combinado    : {len(all_convs)}")
    return all_convs


def build_modelfile(conversations: list[dict], epoch: int) -> str:
    """Genera el Ollama Modelfile con el system prompt + ejemplos baked-in."""

    # JSON Schema como string para incluir en el prompt
    schema_str = json.dumps(LlamaIntent.model_json_schema(), ensure_ascii=False, indent=2)

    catalog_lines = "\n".join(f"- {p['name']} (Bs {p['price']:.2f})" for p in MOCK_PRODUCTS)

    system_prompt = f"""\
Eres un extractor de intención para pedidos de bebidas de AJE Bolivia.
NO eres un chatbot libre. SOLO extraes intenciones y productos de mensajes de preventistas bolivianos.

### Catálogo disponible:
{catalog_lines}

### Reglas críticas:
1. SIEMPRE devuelve JSON válido con EXACTAMENTE este schema. NADA más.
2. No inventes productos que no están en el catálogo.
3. Alcohol (cheba/chela/birra/cerveza/vino/ron/vodka/whisky): intencion="fuera_de_alcance", motivo_rechazo="alcohol"
4. Comida sólida (papas/nachos/pizza/galletas/snack/hamburguesa): intencion="fuera_de_alcance", motivo_rechazo="comida_solida"
5. Si el usuario saluda: intencion="saludo"
6. Si pide ver el menú o catálogo: intencion="consulta_catalogo"
7. Si pide ver todos sus pedidos, historial o pedidos pendientes: intencion="listar_pedidos" (ej. "muéstrame mis pedidos pendientes", "qué pedidos tengo").
8. Si pregunta específicamente por el estado, ubicación o seguimiento de un pedido actual: intencion="estado_pedido" (ej. "cómo va mi pedido?", "dónde está mi entrega?").
9. Si confirma ("sí"/"dale"/"ok"/"listo"/"confirmo"): intencion="confirmacion"
10. Si niega ("no"/"cancelar"/"no gracias"): intencion="negacion"
11. Si el mensaje es una aclaración corta que indica una presentación, volumen o respuesta a una pregunta de tamaño (ej. "de litro", "la de 500", "el de dos litros", "de tres litros", "chico", "el grande", "mediano"):
    - Si el mensaje contiene verbos de pedido (como "quiero", "dame", "manda", "ponme", "trae", "agrega") o marcas/productos del catálogo (como "big", "cola", "cielo", "volt", "oro", "cifrut", "pulp", "free tea", "sporade", "agua"), entonces NUNCA es una aclaración simple, sino un pedido completo. Clasifícalo como intencion="pedido" y extrae el producto.
    - Si NO contiene esos verbos ni marcas, y es solo la frase de tamaño/volumen: establece intencion="aclaracion" y deja la lista de productos vacía (productos=[]), y NO intentes crear un producto con nombre "litro" o similar.
12. Si la presentación es ambigua, marca requiere_aclaracion=true en ese producto.
13. "familiar" / "grande" ≈ 2L. "chico" / "personal" / "chika" ≈ 500ml. "litro" = 1L.
14. "cielito" = Agua Cielo 500ml. "voltcito" = Volt 300ml. "orito" = Oro 500ml. "pulpito" = Pulp 300ml.
15. "pa" = para. "coquita" / "cocaca" = Coca-Cola.

### Schema JSON requerido:
{schema_str}

Epoch {epoch} — modelo entrenado con {len(conversations)} ejemplos bolivianos.\
"""

    lines = [
        f"FROM {BASE_MODEL}",
        "",
        f'SYSTEM """{system_prompt}"""',
        "",
        "PARAMETER temperature 0",
        "PARAMETER num_predict 600",
        "PARAMETER top_p 0.1",
        "PARAMETER top_k 10",
        "",
    ]

    for conv in conversations:
        user_text      = json.dumps(conv["user"], ensure_ascii=False)
        assistant_text = json.dumps(conv["assistant"], ensure_ascii=False)
        lines.append(f"MESSAGE user {user_text}")
        lines.append(f"MESSAGE assistant {assistant_text}")
        lines.append("")

    return "\n".join(lines)


def create_ollama_model(modelfile_content: str, model_name: str) -> bool:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".modelfile",
                                     delete=False, encoding="utf-8") as f:
        f.write(modelfile_content)
        tmpfile = f.name
    try:
        print(color(f"\n  📦 Creando modelo '{model_name}'...", CYAN))
        result = subprocess.run(
            ["ollama", "create", model_name, "-f", tmpfile],
            capture_output=True, text=True, timeout=180
        )
        if result.returncode == 0:
            print(color(f"  ✅ Modelo '{model_name}' creado", GREEN))
            return True
        print(color(f"  ❌ Error: {result.stderr[:300]}", RED))
        return False
    except subprocess.TimeoutExpired:
        print(color("  ⚠️  Timeout al crear el modelo", YELLOW))
        return False
    except FileNotFoundError:
        print(color("  ❌ 'ollama' no encontrado en PATH", RED))
        return False
    finally:
        os.unlink(tmpfile)


async def warmup_model(model_name: str) -> None:
    import app.services.llm as llm_mod
    original = llm_mod.OLLAMA_MODEL
    llm_mod.OLLAMA_MODEL = model_name
    try:
        print(color(f"  🔥 Calentando '{model_name}'...", CYAN))
        await llm_mod.warmup()
        print(color("  ✅ Warmup OK", GREEN))
    finally:
        llm_mod.OLLAMA_MODEL = original


async def evaluate_epoch(conversations: list[dict], epoch: int, model_name: str, sample_size: int) -> dict:
    """Evalúa el modelo sobre una muestra del dataset."""
    sample = conversations[:sample_size]
    total = len(sample)
    intent_ok = product_hits = product_total = qty_ok = qty_total = errors = 0
    latencies = []

    print(color(f"\n  🔍 Evaluando {total} casos con '{model_name}'...", CYAN))

    import app.services.llm as llm_mod
    original = llm_mod.OLLAMA_MODEL
    llm_mod.OLLAMA_MODEL = model_name

    for i, conv in enumerate(sample, 1):
        user_text = conv["user"]
        try:
            expected = json.loads(conv["assistant"])
        except json.JSONDecodeError:
            errors += 1
            continue

        expected_prods = expected.get("productos") or []
        product_total += len(expected_prods)
        qty_total += len(expected_prods)

        t0 = time.time()
        result: LlamaIntent | None = await ask_llm(user_text, MOCK_PRODUCTS)
        latency_ms = (time.time() - t0) * 1000
        latencies.append(latency_ms)

        if result is None:
            errors += 1
            print(color(f"    [{i:02d}] ⚠️  timeout: {user_text[:45]}", YELLOW))
            continue

        # ── Intención ──
        if result.intencion == expected.get("intencion"):
            intent_ok += 1
        else:
            print(color(f"    [{i:02d}] ❌ intent: got={result.intencion!r} want={expected.get('intencion')!r} | {user_text[:40]}", RED))

        # ── Productos y cantidades ──
        detected = result.productos or []
        for ep in expected_prods:
            sku_exp = (ep.get("sku_sugerido") or "").lower()
            name_exp = (ep.get("nombre_detectado") or "").lower()
            qty_exp = ep.get("cantidad", 1)

            found_product = any(
                sku_exp in (dp.sku_sugerido or "").lower() or
                name_exp in (dp.nombre_detectado or "").lower() or
                sku_exp in (dp.nombre_detectado or "").lower()
                for dp in detected
            )
            if found_product:
                product_hits += 1

            found_qty = any(
                abs(dp.cantidad - qty_exp) == 0 for dp in detected
            )
            if found_qty:
                qty_ok += 1

        if i % 5 == 0:
            pct = intent_ok / i * 100
            print(f"    Progreso: {i}/{total} — intent acc: {pct:.0f}%", end="\r")

    llm_mod.OLLAMA_MODEL = original

    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    return {
        "epoch":             epoch,
        "model":             model_name,
        "samples":           total,
        "errors":            errors,
        "intent_accuracy":   round(intent_ok / total * 100, 1) if total > 0 else 0,
        "product_hit_rate":  round(product_hits / product_total * 100, 1) if product_total > 0 else 0,
        "quantity_accuracy": round(qty_ok / qty_total * 100, 1) if qty_total > 0 else 0,
        "avg_latency_ms":    round(avg_latency, 0),
    }


def print_metrics(metrics: dict):
    e = metrics["epoch"]
    ia = metrics["intent_accuracy"]
    pr = metrics["product_hit_rate"]
    qa = metrics["quantity_accuracy"]
    print(color(f"\n  ┌─ Época {e} — {metrics['model']}", BOLD))
    print(f"  │  Muestras: {metrics['samples']}  errores: {metrics['errors']}")
    print(f"  │  Intención: {color(f'{ia}%', GREEN if ia >= 90 else YELLOW if ia >= 75 else RED)}")
    print(f"  │  Producto:  {color(f'{pr}%', GREEN if pr >= 85 else YELLOW if ia >= 70 else RED)}")
    print(f"  │  Cantidad:  {color(f'{qa}%', GREEN if qa >= 85 else YELLOW if qa >= 70 else RED)}")
    print(f"  └  Latencia:  {metrics['avg_latency_ms']}ms")


async def main():
    print(color("\n╔══════════════════════════════════════════════════╗", MAGENTA))
    print(color("║  ENTRENAMIENTO LLaMA — AJE Preventista Bolivia   ║", MAGENTA))
    print(color(f"║  Target: ≥90% intención | ≥85% producto          ║", MAGENTA))
    print(color("╚══════════════════════════════════════════════════╝\n", MAGENTA))

    # 1. Verificar Ollama
    print(color("📡 Verificando Ollama...", BOLD))
    status = await check_ollama_status()
    if not status.get("reachable"):
        print(color("❌ Ollama no disponible. Corre: ollama serve", RED))
        return
    print(color(f"  ✅ Ollama OK — modelo base: {BASE_MODEL}", GREEN))
    print(f"  Schema Pydantic: {len(LlamaIntent.model_json_schema().get('properties', {}))} campos en LlamaIntent\n")

    # 2. Cargar dataset
    print(color("📂 Cargando conversaciones de entrenamiento...", BOLD))
    conversations = load_dataset()

    all_metrics = []

    # 3. Loop de épocas
    for epoch in range(1, EPOCHS + 1):
        print(color(f"\n{'═'*54}", CYAN))
        print(color(f"  ÉPOCA {epoch}/{EPOCHS}", BOLD))
        print(color(f"{'═'*54}", CYAN))

        # Incrementar ejemplos: 50% → 100%
        pct = 0.50 + (epoch - 1) * 0.50
        n_examples = min(len(conversations), max(20, int(len(conversations) * pct)))
        
        # Evaluar ambas épocas en la muestra completa para comparación justa
        sample_eval = min(EVAL_SAMPLE, len(conversations))

        print(f"  Ejemplos en Modelfile  : {n_examples}")
        print(f"  Muestras de evaluación : {sample_eval}")

        modelfile = build_modelfile(conversations[:n_examples], epoch)
        model_name = f"{OUTPUT_MODEL}-e{epoch}"

        if not create_ollama_model(modelfile, model_name):
            print(color(f"  ⚠️  Saltando época {epoch}", YELLOW))
            continue

        await warmup_model(model_name)

        metrics = await evaluate_epoch(conversations, epoch, model_name, sample_eval)
        all_metrics.append(metrics)
        print_metrics(metrics)

        # ── Deshabilitado early stopping para entrenar al máximo y evaluar todas las épocas ──
        # if metrics["intent_accuracy"] >= 92 and metrics["product_hit_rate"] >= 88:
        #     print(color(f"\n  🎯 Objetivo superado en época {epoch}! Deteniendo.", GREEN))
        #     break

    # 4. Resumen
    print(color(f"\n{'═'*54}", MAGENTA))
    print(color("  RESUMEN DE ÉPOCAS", BOLD))
    print(color(f"{'═'*54}", MAGENTA))

    if not all_metrics:
        print(color("No hay métricas.", RED))
        return

    print(f"\n  {'Época':>5}  {'Intención':>10}  {'Producto':>9}  {'Cantidad':>9}  {'Latencia':>9}")
    print(f"  {'─'*5}  {'─'*10}  {'─'*9}  {'─'*9}  {'─'*9}")

    best = max(all_metrics, key=lambda m: m["intent_accuracy"] * 0.5 + m["product_hit_rate"] * 0.35 + m["quantity_accuracy"] * 0.15)

    for m in all_metrics:
        marker = color(" ◄ MEJOR", GREEN) if m["epoch"] == best["epoch"] else ""
        ia_c = color(f"{m['intent_accuracy']:>9}%", GREEN if m["intent_accuracy"] >= 90 else YELLOW)
        pr_c = color(f"{m['product_hit_rate']:>8}%", GREEN if m["product_hit_rate"] >= 85 else YELLOW)
        qa_c = color(f"{m['quantity_accuracy']:>8}%", GREEN if m["quantity_accuracy"] >= 85 else YELLOW)
        print(f"  {m['epoch']:>5}  {ia_c}  {pr_c}  {qa_c}  {m['avg_latency_ms']:>7}ms{marker}")

    # 5. Crear modelo final
    best_epoch = best["epoch"]
    step_coef = (1.0 - 0.50) / (EPOCHS - 1) if EPOCHS > 1 else 0
    best_n = min(len(conversations), max(20, int(len(conversations) * (0.50 + (best_epoch - 1) * step_coef))))
    print(color(f"\n🏆 Creando modelo final '{OUTPUT_MODEL}' con {best_n} ejemplos (época {best_epoch})...", BOLD))

    final_modelfile = build_modelfile(conversations[:best_n], epoch=best_epoch)
    if create_ollama_model(final_modelfile, OUTPUT_MODEL):
        ia = best["intent_accuracy"]
        pr = best["product_hit_rate"]
        goal_met = ia >= 90 and pr >= 85
        print(color(f"\n{'✅' if goal_met else '⚠️ '} Modelo final listo: '{OUTPUT_MODEL}'", GREEN if goal_met else YELLOW))
        print(f"   Intención accuracy : {ia}%  {'✅' if ia >= 90 else '❌ (objetivo: ≥90%)'}")
        print(f"   Producto hit rate  : {pr}%  {'✅' if pr >= 85 else '❌ (objetivo: ≥85%)'}")
        print()
        print(color("   Para activarlo, actualiza .env:", BOLD))
        print(f"   OLLAMA_MODEL={OUTPUT_MODEL}")
        print()
        print(color("   Limpieza (modelos de época):", BOLD))
        for ep in range(1, EPOCHS + 1):
            print(f"   ollama rm {OUTPUT_MODEL}-e{ep}")

    print(color("\n╔══════════════════════════════════════════════════╗", MAGENTA))
    print(color("║  Entrenamiento completado                        ║", MAGENTA))
    print(color("╚══════════════════════════════════════════════════╝\n", MAGENTA))


if __name__ == "__main__":
    asyncio.run(main())
