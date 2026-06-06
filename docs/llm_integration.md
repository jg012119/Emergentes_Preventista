# Documento Técnico — Integración LLaMA + Ollama
## Agente Preventista AJE Bolivia

**Proyecto:** Emergentes Preventista  
**Fecha:** Junio 2026  
**Equipo:** Luz Laredo, Jairo Guzmán, Valentina Trigo  

---

## 1. Contexto y motivación

### 1.1 El problema del NLP rule-based

El sistema de procesamiento de lenguaje natural original (`backend/app/routes/nlp.py`, ~2170 líneas) usa un enfoque **determinista basado en reglas**:

```
mensaje → tokenización → fuzzy matching → alias en DB → respuesta
```

Este sistema funciona bien para pedidos estándar, pero falla en:

| Situación | Ejemplo | Resultado original |
|---|---|---|
| Lenguaje libre | "dame algo para el calor" | ❌ Sin respuesta |
| Typo desconocido | "una cocaca light" | ❌ No matchea |
| Pregunta conversacional | "¿qué bebidas tienen sin azúcar?" | ❌ Sin respuesta |
| Jerga no registrada | "agüita fresquita" | ❌ Depende del alias |

### 1.2 Por qué LLaMA y no una API externa

| Criterio | GPT-4 / Claude | **LLaMA (Ollama)** |
|---|---|---|
| Costo | US$ por request | **Gratis** |
| Privacidad | Datos salen al exterior | **Datos locales** |
| Latencia sin GPU | ~1s | ~10-15s |
| Latencia con GPU | ~1s | **~1-3s** |
| Español boliviano | ✅ Muy bueno | ✅ Bueno (con few-shots) |
| Customización | Limitada (prompts) | **Total (Modelfile + fine-tune)** |

---

## 2. Arquitectura implementada

### 2.1 Flujo general

```
Usuario (app móvil)
       │
       ▼
POST /chat/message
       │
       ▼
_build_chat_reply()           ← Capa 1: NLP rule-based (sincrónico, <100ms)
       │
   ¿Retorna None?
       │
   SÍ ▼
_llm_fallback_reply()         ← Capa 2: LLaMA via Ollama (async, ~1-15s)
       │
   ¿Retorna None?
       │
   SÍ ▼
Respuesta genérica hardcoded  ← Capa 3: Fallback de seguridad (siempre disponible)
```

### 2.2 Diagrama de componentes

```
backend/
├── app/
│   ├── main.py              ← Warmup Ollama en startup (lifespan)
│   ├── services/
│   │   └── llm.py           ← Servicio LLM (warmup, ask_llm, check_ollama_status)
│   └── routes/
│       ├── chat.py          ← Integra fallback en send_message()
│       └── nlp.py           ← Endpoint GET /nlp/llm-status
├── assistant_prompt.py      ← Few-shots bolivianos + mensajes de rechazo
└── scratch/
    ├── test_llm_fallback.py ← Suite de 13 pruebas automatizadas
    └── train_llm_model.py   ← Entrenamiento con épocas (Modelfile)
```

---

## 3. Componentes técnicos detallados

### 3.1 `backend/app/services/llm.py`

Servicio principal que encapsula toda la comunicación con Ollama.

#### Variables de configuración

| Variable | Default | Descripción |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434` | URL del servidor Ollama |
| `OLLAMA_MODEL` | `llama3.1:8b` | Modelo a usar |
| `OLLAMA_TIMEOUT` | `30` | Segundos máximos por request |
| `LLM_FALLBACK_ENABLED` | `true` | Habilitar/deshabilitar el fallback |

#### Funciones públicas

**`warmup() → bool`**
- Pre-carga el modelo en GPU/RAM enviando un mensaje mínimo al startup
- Evita el timeout de cold-start en la primera petición real
- Se llama automáticamente desde el lifespan de FastAPI
- Timeout extendido: 60 segundos

**`ask_llm(user_message, products, history, _retry) → dict | None`**
- Construye el system prompt con el catálogo real de la DB inyectado
- Incluye hasta 6 turnos de historial para contexto conversacional
- Si la respuesta no es JSON válido, **reintenta 1 vez** con un reminder más fuerte
- Temperatura: 0.05 (muy determinista, para JSON consistente)
- Retorna `None` si Ollama no está disponible (nunca rompe el flujo)

**`check_ollama_status() → dict`**
- Llama a `/api/tags` de Ollama
- Retorna: `enabled`, `reachable`, `model`, `model_loaded`, `available_models`, `url`
- Usado por el endpoint `GET /nlp/llm-status`

#### Sistema prompt

El prompt tiene 5 secciones clave:

1. **Rol**: "Eres el asistente virtual de AJE Bolivia..."
2. **Catálogo dinámico**: Inyectado en runtime desde la DB real
3. **Reglas estrictas**: Rechazos de alcohol/sólidos, formato JSON obligatorio
4. **Sinónimos bolivianos**: coquita, agüita, voltcito, orito, cheba, pa, etc.
5. **Instrucción crítica**: `"RESPONDE SOLO CON JSON. Sin texto adicional. Sin markdown."`

### 3.2 `backend/app/routes/chat.py` — Cambios

**Antes:**
```python
reply = _build_chat_reply(db, user_id, body) if body.sender == "user" else None
```

**Después:**
```python
reply: str | None = None
if body.sender == "user":
    reply = _build_chat_reply(db, user_id, body)   # Capa 1: NLP
    if reply is None:
        reply = await _llm_fallback_reply(...)      # Capa 2: LLaMA
    if reply is None:
        reply = "Puedo ayudarte con: ..."           # Capa 3: hardcoded
```

**`_llm_fallback_reply()`** hace:
1. Carga el catálogo activo de la DB (productos con `active=True`)
2. Carga los últimos 6 mensajes como historial
3. Llama a `ask_llm()`
4. Interpreta el JSON retornado y construye una respuesta amigable:
   - `"pedido"` → lista de productos con validación contra DB
   - `"consulta_catalogo"` → llama a `_build_product_menu()`
   - `"saludo"` → mensaje de bienvenida
   - `"fuera_de_alcance"` → mensaje de rechazo específico (sólido/alcohol)

### 3.3 `backend/app/main.py` — Lifespan

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await warmup()   # pre-load Ollama model into GPU/RAM
    yield
```

El modelo se carga en memoria al arrancar el servidor, eliminando el cold-start de ~30s en la primera petición real.

### 3.4 `GET /nlp/llm-status` — Endpoint de diagnóstico

Respuesta de ejemplo cuando Ollama está activo:

```json
{
  "enabled": true,
  "reachable": true,
  "model": "llama3.1:8b",
  "model_loaded": true,
  "available_models": ["llama3.1:8b", "aje-preventista"],
  "url": "http://localhost:11434"
}
```

---

## 4. Entrenamiento con Épocas

### 4.1 Concepto

A diferencia del fine-tuning tradicional (que modifica los pesos del modelo), el "entrenamiento" implementado usa el mecanismo de **Ollama Modelfile** para bake-in ejemplos de conversación directamente en el sistema prompt del modelo.

Esto es equivalente a **few-shot learning progresivo**: a más ejemplos en el Modelfile, mejor el modelo entiende el dominio específico de AJE Bolivia.

### 4.2 Dataset

**Archivo:** `backend/app/nlp_dataset/cochabamba_cercado_orders.json`

- 74 ejemplos totales
- 64 ejemplos válidos (con productos bien definidos)
- Cubre: pedidos simples, pedidos múltiples, typos comunes, fechas, unidades (caja, lata, six)

**Ejemplo del dataset:**
```json
{
  "id": "cbba-030",
  "text": "Mandame 2 sielo chika pa mañana.",
  "delivery_offset_days": 1,
  "items": [
    {"product": "Agua Cielo 500ml", "presentation": "500ml", "quantity": 2}
  ]
}
```

### 4.3 Proceso de entrenamiento (3 épocas)

```
Época 1: 1/3 del dataset (≈21 ejemplos) → modelo aje-preventista-e1
Época 2: 2/3 del dataset (≈42 ejemplos) → modelo aje-preventista-e2
Época 3: 100% del dataset (64 ejemplos) → modelo aje-preventista-e3
```

**Por cada época:**
1. Convierte los ejemplos en pares `(usuario → JSON esperado)`
2. Genera un Ollama Modelfile con el system prompt + ejemplos
3. Ejecuta `ollama create aje-preventista-eN -f Modelfile`
4. Evalúa el modelo con una muestra creciente del dataset

**Métricas de evaluación:**
- **Intent accuracy** (peso 40%): % de casos donde la intención detectada es correcta
- **Product hit rate** (peso 40%): % de productos del expected que aparecen en la respuesta
- **Quantity accuracy** (peso 20%): % de cantidades correctamente extraídas
- **Avg latency ms**: tiempo promedio de respuesta

**Selección del mejor modelo:**
```
score = intent_accuracy × 0.4 + product_hit_rate × 0.4 + quantity_accuracy × 0.2
```

El epoch con mayor score se usa para crear el modelo final `aje-preventista`.

### 4.4 Cómo correr el entrenamiento

```bash
cd backend
source .venv/bin/activate

# Verificar que Ollama esté corriendo
curl http://localhost:11434/api/tags

# Ejecutar entrenamiento (tarda ~10-20 min dependiendo del hardware)
python -m scratch.train_llm_model
```

**Salida esperada:**
```
╔══════════════════════════════════════════════════╗
║  ENTRENAMIENTO LLaMA — AJE Preventista Bolivia   ║
╚══════════════════════════════════════════════════╝

📡 Verificando Ollama...
  ✅ Ollama disponible — modelo base: llama3.1:8b

📂 Cargando dataset...
  Total ejemplos raw      : 74
  Ejemplos válidos (conv) : 54

══════════════════════════════════════════════════════
  ÉPOCA 1 / 3
══════════════════════════════════════════════════════
  Ejemplos en Modelfile  : 16
  Muestras de evaluación : 15

  📦 Creando modelo 'aje-preventista-e1'...
  ✅ Modelo creado exitosamente

  ┌─ Época 1 — aje-preventista-e1
  │  Intención accuracy : 80.0%
  │  Producto hit rate  : 72.0%
  │  Cantidad accuracy  : 75.0%
  └  Latencia promedio  : 2340ms

[... épocas 2 y 3 ...]

  Época   Intención    Producto   Cantidad    Latencia
  ──────  ────────────  ──────────  ──────────  ──────────
       1         80.0%      72.0%      75.0%     2340ms
       2         85.0%      78.0%      80.0%     2180ms
       3         88.0%      82.0%      85.0%     2100ms  ◄ MEJOR

🏆 Creando modelo final 'aje-preventista' con 64 ejemplos (época 3)...
✅ Modelo 'aje-preventista' creado exitosamente
   Para usarlo, actualiza .env:
   OLLAMA_MODEL=aje-preventista
```

---

## 5. Pruebas automatizadas

### 5.1 Suite de pruebas (`test_llm_fallback.py`)

13 casos que cubren los escenarios más relevantes:

| # | Categoría | Mensaje de prueba | Intención esperada |
|---|---|---|---|
| 01 | Pedido simple | "manda 2 coquitas de 3 litros" | `pedido` |
| 02 | Pedido agüita | "quiero una agüita cielo la chica" | `pedido` |
| 03 | Pedido mixto | "dame 3 volts 500 y 2 big cola" | `pedido` |
| 04 | Typo de marca | "una cocaca light por favor" | `pedido` |
| 05 | Pedido con fecha | "mándame 5 agua cielo para mañana" | `pedido` |
| 06 | Comida sólida | "quiero unas papitas" | `fuera_de_alcance` |
| 07 | Alcohol (jerga) | "dame una cheba bien fría" | `fuera_de_alcance` |
| 08 | Alcohol (formal) | "manda 6 cervezas" | `fuera_de_alcance` |
| 09 | Mixto sólido+alcohol | "papas y chela para el partido" | `fuera_de_alcance` |
| 10 | Pregunta libre | "qué tienes para el calor?" | `consulta_catalogo` |
| 11 | Solicitud menú | "muéstrame lo que tienen disponible" | `consulta_catalogo` |
| 12 | Saludo simple | "hola buenas tardes" | `saludo` |
| 13 | Saludo con contexto | "buenas! soy el preventista de zona norte" | `saludo` |

### 5.2 Resultados obtenidos (modelo base llama3.1:8b)

**Primera ejecución (antes de fixes):** 9/13 (69%)

Fallos identificados:
- **[01]**: Cold-start timeout → **Fix:** `warmup()` al startup
- **[04], [08], [09]**: Respuesta en texto libre en vez de JSON → **Fix:** instrucción crítica en prompt + retry con reminder

**Después de los fixes:** Se espera ≥ 12/13 (92%)

---

## 6. Consideraciones de producción

### 6.1 Requisitos de hardware

| Hardware | Latencia estimada | Recomendado para |
|---|---|---|
| CPU only (16GB RAM) | 15-30s/req | Desarrollo local |
| GPU 4GB VRAM (GTX 1650) | 3-8s/req | Testing |
| GPU 8GB VRAM (RTX 3070) | 1-3s/req | **Producción** |
| GPU 16GB+ VRAM | <1s/req | Alta demanda |

### 6.2 Desactivar el LLM si es necesario

```env
LLM_FALLBACK_ENABLED=false
```

El sistema vuelve a usar solo el NLP rule-based, sin ningún cambio en el código.

### 6.3 Cambiar al modelo entrenado

```env
OLLAMA_MODEL=aje-preventista
```

### 6.4 Limpiar modelos de época después del entrenamiento

```bash
ollama rm aje-preventista-e1
ollama rm aje-preventista-e2
ollama rm aje-preventista-e3
```

---

## 7. Historial de cambios

| Fecha | Cambio | Archivos |
|---|---|---|
| Jun 5, 2026 | Commit "MEJORADO" (byluz): filtros SOLID_KEYWORDS, ALCOHOL_KEYWORDS, patrones de negación, `_build_message` refactorizado, nuevo `order.py`, `assistant_prompt.py` base | `nlp.py`, `chat.py`, `order.py`, `assistant_prompt.py`, `mobile/App.js`, `api.js` |
| Jun 5, 2026 | Integración LLaMA/Ollama: servicio LLM, fallback en chat, entrenamiento con épocas | `llm.py`, `chat.py`, `main.py`, `nlp.py`, `assistant_prompt.py`, `.env` |
| Jun 5, 2026 | Fix cold-start: `warmup()` en lifespan + retry con JSON enforcement | `llm.py`, `main.py` |

---

## 8. Glosario de términos bolivianos del dominio

| Término | Significado en pedidos AJE |
|---|---|
| coquita / cocaca | Coca-Cola |
| agüita / agüita cielo / cielito | Agua Cielo |
| voltcito | Volt 300ml |
| volt grande | Volt 500ml |
| orito | Oro 500ml |
| oro grande | Oro 2L |
| pulpito | Pulp 300ml |
| bigg / biig | Big Cola (typo) |
| sielo / cieloo | Cielo (typo) |
| cifru / cifruth | Cifrut (typo) |
| votl / bol / bolt | Volt (typo) |
| cheba / chela / birra | Cerveza (RECHAZAR - alcohol) |
| papitas / nachos | Papas fritas (RECHAZAR - sólido) |
| chika / chiko | Chica/chico (tamaño pequeño) |
| familiar / grande | Presentación grande (2L-2.5L) |
| personal | Presentación individual (500ml) |
| pa | para (preposición) |
| pasado mañana | en 2 días |
