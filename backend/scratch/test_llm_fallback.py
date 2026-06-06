"""
Test script for the LLM fallback service (Ollama + llama3.1:8b).

Run from the backend/ directory:
    python -m scratch.test_llm_fallback

Prerequisites:
    1. Ollama running:  ollama serve
    2. Model pulled:    ollama pull llama3.1:8b  (or aje-preventista)
    3. Backend venv active with httpx installed
"""

import asyncio
import json
import sys
import os

# Allow running from backend/ directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm import ask_llm, check_ollama_status, build_catalog_text
from app.models.schemas import LlamaIntent

# ---------------------------------------------------------------------------
# Mock catalog — mirrors typical products in the AJE Bolivia DB
# ---------------------------------------------------------------------------
MOCK_PRODUCTS = [
    {"id": "1", "name": "Coca-Cola Normal 3L",    "price": 12.50, "stock": 100},
    {"id": "2", "name": "Coca-Cola Normal 1.5L",  "price":  7.00, "stock": 80},
    {"id": "3", "name": "Coca-Cola Normal 500ml",  "price":  3.50, "stock": 200},
    {"id": "4", "name": "Agua Cielo 600ml",         "price":  2.00, "stock": 150},
    {"id": "5", "name": "Agua Cielo 2L",            "price":  5.00, "stock": 60},
    {"id": "6", "name": "Volt 300ml",               "price":  4.00, "stock": 90},
    {"id": "7", "name": "Volt 500ml",               "price":  6.00, "stock": 70},
    {"id": "8", "name": "Big Cola 3L",              "price": 10.00, "stock": 50},
    {"id": "9", "name": "Pulp Naranja 1L",          "price":  6.50, "stock": 40},
    {"id":"10", "name": "Cifrut Naranja 500ml",     "price":  3.50, "stock": 110},
]

# ---------------------------------------------------------------------------
# Test cases: (description, message, expected_intencion)
# ---------------------------------------------------------------------------
TEST_CASES = [
    # Pedidos normales
    ("Pedido simple",             "manda 2 coquitas de 3 litros",               "pedido"),
    ("Pedido con agüita",         "quiero una agüita cielo la chica",           "pedido"),
    ("Pedido coloquial mixto",    "dame 3 volts 500 y 2 big cola",              "pedido"),
    ("Typo en marca",             "una cocaca light por favor",                 "pedido"),
    ("Pedido con fecha",          "mándame 5 agua cielo para mañana",           "pedido"),

    # Fuera de alcance
    ("Comida sólida - papitas",   "quiero unas papitas",                        "fuera_de_alcance"),
    ("Alcohol - cheba",           "dame una cheba bien fría",                   "fuera_de_alcance"),
    ("Alcohol - cerveza",         "manda 6 cervezas",                           "fuera_de_alcance"),
    ("Sólido + alcohol mixto",    "papas y chela para el partido",              "fuera_de_alcance"),

    # Consultas
    ("Pregunta libre - calor",    "qué tienes para el calor?",                  "consulta_catalogo"),
    ("Solicitud de menú",         "muéstrame lo que tienen disponible",         "consulta_catalogo"),

    # Saludos
    ("Saludo simple",             "hola buenas tardes",                         "saludo"),
    ("Saludo con nombre",         "buenas! soy el preventista de zona norte",   "saludo"),
]


def color(text: str, code: int) -> str:
    return f"\033[{code}m{text}\033[0m"

GREEN  = 32
RED    = 31
YELLOW = 33
CYAN   = 36
BOLD   = 1


async def run_tests():
    print(color("\n═══════════════════════════════════════════", CYAN))
    print(color("  TEST: LLM Fallback — Ollama (Pydantic LlamaIntent)", BOLD))
    print(color("═══════════════════════════════════════════\n", CYAN))

    # Check Ollama status first
    status = await check_ollama_status()
    print(color("📡 Estado de Ollama:", BOLD))
    print(json.dumps(status, indent=2, ensure_ascii=False))
    print()

    if not status.get("reachable"):
        print(color("❌ Ollama no está disponible. Asegúrate de correr: ollama serve", RED))
        print(color("   Luego: ollama pull llama3.1:8b", RED))
        return

    if not status.get("model_loaded"):
        print(color(f"⚠️  El modelo '{status.get('model')}' no está descargado.", YELLOW))
        print(color(f"   Ejecuta: ollama pull {status.get('model')}", YELLOW))
        print(color("   Continuando de todas formas...\n", YELLOW))

    print(color(f"📋 Catálogo de prueba ({len(MOCK_PRODUCTS)} productos):", BOLD))
    print(build_catalog_text(MOCK_PRODUCTS))
    print()

    # Show the Pydantic schema being used for structured output
    print(color("📐 Schema Pydantic usado para Ollama structured output:", BOLD))
    schema = LlamaIntent.model_json_schema()
    print(f"   Campos: {list(schema.get('properties', {}).keys())}")
    print()

    passed = 0
    failed = 0
    errors = 0

    for i, (desc, message, expected) in enumerate(TEST_CASES, 1):
        print(color(f"[{i:02d}] {desc}", BOLD))
        print(f"     Mensaje: \"{message}\"")

        try:
            result: LlamaIntent | None = await ask_llm(message, MOCK_PRODUCTS)
            if result is None:
                print(color("     ⚠️  LLM retornó None (timeout o Ollama no disponible)", YELLOW))
                errors += 1
                print()
                continue

            # LlamaIntent is a Pydantic model — access with dot notation
            intencion = result.intencion
            productos = result.productos or []
            motivo    = result.motivo_rechazo
            libre     = result.mensaje_libre
            confianza = result.confianza

            ok = intencion == expected
            status_icon = color("✅ PASS", GREEN) if ok else color("❌ FAIL", RED)
            print(f"     {status_icon}  intención={intencion!r}  esperada={expected!r}  confianza={confianza:.2f}")

            if productos:
                for p in productos:
                    # LlamaProduct is also a Pydantic model
                    print(f"       → {p.nombre_detectado!r:30s} "
                          f"x{p.cantidad}  pres={p.presentacion}  "
                          f"sku={p.sku_sugerido!r}  "
                          f"aclaracion={p.requiere_aclaracion}")

            if motivo:
                print(f"       motivo_rechazo: {motivo}")
            if libre:
                print(f"       mensaje_libre: {libre[:120]}")
            if result.requiere_aclaracion and result.pregunta_aclaracion:
                print(f"       pregunta: {result.pregunta_aclaracion}")
            if result.fecha_entrega:
                print(f"       fecha_entrega: {result.fecha_entrega}")

            if ok:
                passed += 1
            else:
                failed += 1

        except Exception as exc:
            print(color(f"     💥 Excepción: {exc}", RED))
            import traceback
            traceback.print_exc()
            errors += 1

        print()

    total = passed + failed + errors
    print(color("═══════════════════════════════════════════", CYAN))
    print(color(f"  Resultados: {passed}/{total} pasaron", GREEN if passed == total else YELLOW))
    if failed:
        print(color(f"  Fallidos:   {failed}", RED))
    if errors:
        print(color(f"  Errores:    {errors}", YELLOW))
    print(color("═══════════════════════════════════════════\n", CYAN))


if __name__ == "__main__":
    asyncio.run(run_tests())
