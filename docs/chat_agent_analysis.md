# Análisis Completo del Agente de Chat — Preventista AJE Bolivia

> **Proyecto:** Emergentes Preventista  
> **Archivo central:** `backend/app/routes/chat.py`  
> **Fecha:** Junio 2026

---

## 1. Visión General

El agente del chat es el **cerebro conversacional** del sistema. Su trabajo es recibir mensajes de texto libre de un preventista desde la app móvil y convertirlos en acciones concretas: crear borradores de pedidos, mostrar el catálogo, listar pedidos existentes, confirmar transacciones, o rechazar solicitudes fuera del dominio de AJE Bolivia.

No es un chatbot genérico. Está diseñado específicamente para interpretar **español boliviano coloquial** de vendedores que operan en zonas urbanas de Cochabamba y comunican sus pedidos de manera informal, con jerga local, errores ortográficos y frases incompletas.

El punto de entrada para todos los mensajes del chat es:

```
POST /chat/message
```

Definido en `backend/app/routes/chat.py` → función `send_message()` (línea 512).

---

## 2. Arquitectura de 3 Capas

Cuando llega un mensaje del usuario, el backend lo procesa secuencialmente por tres niveles de resolución. Si una capa produce una respuesta, las capas inferiores no se ejecutan:

```
Mensaje del preventista
         │
         ▼
┌────────────────────────────────────────────┐
│  CAPA 1: NLP de Reglas                     │  < 100ms
│  Lógica determinista + Fuzzy Matching       │  Síncrona
│  chat.py → _build_chat_reply()             │
└──────────────────────┬─────────────────────┘
                       │ Retorna None si no puede resolver
                       ▼
┌────────────────────────────────────────────┐
│  CAPA 2: Fallback LLM                      │  1–15s según hardware
│  LLaMA 3.1 8B via Ollama local             │  Asíncrona (await)
│  chat.py → _llm_fallback_reply()           │
└──────────────────────┬─────────────────────┘
                       │ Retorna None si Ollama falla o no responde
                       ▼
┌────────────────────────────────────────────┐
│  CAPA 3: Mensaje Hardcoded                 │  0ms
│  Mensaje fijo de ayuda                     │  Siempre disponible
└────────────────────────────────────────────┘
```

---

## 3. CAPA 1 — NLP de Reglas Detallado

### 3.1 Función principal: `_build_chat_reply()`

**Archivo:** `backend/app/routes/chat.py`, línea 308.

Esta función toma el cuerpo del mensaje y ejecuta una serie de condiciones en **orden de prioridad**. En cuanto una condición coincide, retorna una respuesta y detiene el resto:

#### PASO 0 — Mensajes estructurados del catálogo (bypass total)
```python
if _is_structured_order_message(body.message):
    return None
```
Si el mensaje empieza con `"pedido estructurado desde catalogo:"`, fue generado por la pantalla de catálogo de la app móvil y se envía directamente al parser de órdenes sin pasar por el chat. La función retorna `None` deliberadamente para que no se duplique la respuesta.

#### PASO 1 — Normalización del texto
```python
text = _normalize_text(body.message)
```
Convierte el mensaje a minúsculas, elimina acentos/diacríticos (`mañana` → `manana`), reemplaza guiones bajos por espacios y colapsa espacios múltiples. **Todo el procesamiento posterior opera sobre este texto normalizado.**

#### PASO 2 — Negaciones puras
```python
if text in _PURE_NEGATION_NORMALIZED:
    return "Entendido, sin problema. Avisame cuando necesites algo."
```
Si el mensaje normalizado es exactamente una de: `no`, `no gracias`, `no por ahora`, `no quiero nada`, `ninguno`, `nada`, `no nada`, `no quiero`, `no necesito` → responde con un mensaje de cierre amable y termina.

#### PASO 3 — Confirmación de pedido activo
```python
active_order_id = body.order_id or (body.context or {}).get("active_order_id")
if active_order_id and _is_confirmation_message(text):
    return _confirm_active_order_message(db, user_id, active_order_id)
```
Si el frontend envía el ID de un borrador activo en el cuerpo del mensaje, y el texto contiene palabras de confirmación, el sistema ejecuta `_confirm_active_order_message()`:
- Cambia el estado del pedido de `borrador` → `pendiente`
- Devuelve al usuario un resumen con número de pedido, tienda, fecha de entrega y total

**Palabras de confirmación que activan esto:**
```
si, ok, okay, dale, confirmar, pagar, acabar, listo, terminar,
finalizar, finaliza, finalizo, confirmo, confirmado, confirmar pedido,
enviar, enviar pedido, perfecto, esta perfecto, esta bien, todo bien, correcto
```

#### PASO 4 — Comandos de finalización explícitos
```python
if _is_finalization_command(text):
    return _confirm_active_order_message(db, user_id, active_order_id)
```
Un subconjunto de las palabras de confirmación más explícitas (`finalizar`, `confirmar pedido`, `enviar pedido`) disparan la confirmación incluso si no se mandó `active_order_id` en el cuerpo.

#### PASO 5 — Solicitud de menú/catálogo
```python
if "menu" in text or "catalogo" in text or "productos" in text:
    return _build_product_menu(db, user_id)
```
`_build_product_menu()` consulta la base de datos y genera un listado categorizado de todos los productos activos con precios. Personaliza el saludo con el primer nombre del usuario.

#### PASO 6 — Consulta de estado de pedido
```python
if "estado" in text or "seguimiento" in text or "como va" in text:
    return _order_status_message(db, user_id, body.order_id)
```
Busca el último pedido del usuario (o el específico si se pasa `order_id`) y devuelve: estado, sucursal, fecha de entrega, cantidad de productos y total.

#### PASO 7 — Lista de pedidos
```python
if "lista" in text or "ordenes" in text:
    return _list_orders_message(db, user_id, status_filter)
```
Muestra los últimos 5 pedidos. Puede filtrar por estado si el mensaje contiene palabras como `pendientes`, `confirmados`, `rechazados`, `en proceso`, `pagados` (detectadas por `_find_status_filter()`).

#### PASO 8 — Filtro de estado directo
```python
if status_filter:
    return _list_orders_message(db, user_id, status_filter)
```
Si el mensaje contiene directamente un estado sin decir "lista" (ej: "los confirmados"), igual muestra la lista filtrada.

#### PASO 9 — Redirección por negación ("no quiero X, solo Y")
```python
redirect_text = _get_redirect_text(body.message)
if redirect_text:
    nlp_reply = draft_order_chat_reply(db, text=redirect_text, ...)
    if nlp_reply:
        return nlp_reply
```
Si el mensaje tiene el patrón "no quiero [producto], solo [otro_producto]", extrae la parte después de "solo" y la pasa al parser de órdenes como si fuera un pedido fresco. Ejemplo: *"no quiero volt, solo coca"* → el sistema procesa como si el usuario dijera *"coca"*.

#### PASO 10 — Parser de órdenes NLP (el motor principal)
```python
nlp_reply = draft_order_chat_reply(db, text=body.message, user_id=user_id, ...)
if nlp_reply:
    return nlp_reply
```
Invoca el motor de análisis de pedidos ubicado en `backend/app/routes/nlp.py`. Este es el corazón del NLP de reglas. Si detecta productos válidos, crea un borrador de pedido y devuelve el mensaje de confirmación al usuario. Detallado en la sección 4.

#### PASO 11 — Confirmación tardía
```python
if _is_confirmation_message(text):
    return _confirm_active_order_message(db, user_id, active_order_id)
```
Segunda verificación de confirmación: si el NLP de órdenes no resolvió nada pero el texto es una confirmación, intenta confirmar cualquier borrador activo disponible.

#### PASO 12 — Pedidos con palabra "pedido"
```python
if "pedido" in text or "pedidos" in text:
    return _list_orders_message(db, user_id, status_filter)
```
Si el texto contiene la palabra "pedido" pero no coincidió con nada anterior, muestra la lista de pedidos.

#### PASO 13 — Señal al fallback LLM
```python
return None  # signal to the async handler to try LLM
```
Si ninguna condición anterior coincidió, la función retorna `None` explícitamente. Esto le indica a `send_message()` que debe activar la Capa 2 (LLM).

---

## 4. Motor de Análisis de Pedidos NLP — `draft_order_chat_reply()`

**Archivo:** `backend/app/routes/nlp.py`, línea 2019.

Este es el motor de matching de productos. Procesa el texto en cascada:

### 4.1 Pre-procesamiento del texto de entrada

El NLP aplica una serie de transformaciones al texto antes de buscar productos:

**1. Corrección de typos hardcodeados** (`TYPO_REPLACEMENTS` en línea 228):
```
chika     → chica       chiko   → chico
grnade    → grande      grand   → grande
litrso    → litros      litors  → litros
sielo     → cielo       siello  → cielo
cifru     → cifrut      cifruth → cifrut
votl      → volt        vol     → volt
bolt      → volt        bol     → volt
pulpp     → pulp        bigg    → big
```

**2. Eliminación de verbos de petición** (`FILLER_RE`):
Elimina prefijos como `quiero`, `necesito`, `dame`, `manda`, `mandame`, `mandale`, `agrega`, `agregame`, `anotame`, `pasame`, `dejame`, `llevame`, `despachame` al inicio del mensaje.

**3. Extracción de fechas de entrega** (`DATE_TRAILING_RE` + `dateparser`):
Busca patrones como `para mañana`, `para el viernes`, `para pasado mañana` y extrae la fecha separándola del nombre del producto.

### 4.2 Matching de productos

El motor busca productos mediante **fuzzy matching** utilizando `rapidfuzz`:

- **`AUTO_ACCEPT_SCORE = 90`**: Si la similitud entre el texto del usuario y un nombre de producto (o sus aliases) es ≥ 90, el producto se acepta automáticamente sin preguntar al usuario.
- **`CONFIRM_SCORE = 70`**: Si la similitud está entre 70 y 89, el producto se acepta pero se nota como una coincidencia aproximada.
- **`AMBIGUOUS_GAP = 5`**: Si dos candidatos tienen scores separados por menos de 5 puntos, el sistema lo marca como ambiguo y pregunta al usuario qué producto quería.

### 4.3 Detección de cantidades

El motor detecta cantidades de dos formas:
- **Números dígitos**: `2`, `3`, `10`, etc.
- **Números escritos** (`QUANTITY_WORDS`): `un`, `una`, `dos`, `tres`, `cuatro`, ..., `doce`, `docena`.

### 4.4 Detección de presentaciones (tamaños)

Detecta el tamaño del envase mediante `PRESENTATION_RE`:
- Formato numérico con unidad: `500ml`, `2L`, `1.5l`, `3 litros`
- Tokens cualitativos → se mapean a tamaños:
  - `chica/chico/chika/personal` → 500ml
  - `familiar/grande` → 2L o 2.5L según el producto
  - `litro` → 1L
  - `litro y medio` → 1.5L

### 4.5 Resolución de aclaraciones pendientes

Si el usuario no especificó algo en el mensaje anterior (cantidad, tienda, fecha), el backend guardó una "clarificación pendiente" en la base de datos (`nlp_clarifications`). Cuando el usuario responde con información adicional, `_is_clarification_reply()` detecta que el nuevo mensaje parece una respuesta (no un nuevo pedido) y `_matching_pending_clarification()` lo enlaza con la pregunta abierta.

Las clarificaciones expiran automáticamente después de **180 segundos** (`MAX_CLARIFICATION_AGE_SECONDS`).

---

## 5. CAPA 2 — Fallback LLM Detallado

### 5.1 Función: `_llm_fallback_reply()`

**Archivo:** `backend/app/routes/chat.py`, línea 398.

Se ejecuta solo cuando `_build_chat_reply()` retorna `None`. Es una función `async` porque hace llamadas HTTP al servidor de Ollama local.

**Pasos internos:**

1. **Carga el catálogo real desde la DB**:
   ```python
   products = db.table("products").select("id, name, price, stock")
                .eq("active", True).execute().data
   ```
   Solo productos activos. Este catálogo se inyecta dinámicamente en el system prompt del LLM para evitar que alucine con productos inexistentes.

2. **Carga el historial de conversación**:
   ```python
   recent_msgs = db.table("chat_messages")
                   .select("message, sender")
                   .eq("user_id", user_id)
                   .order("created_at", desc=True)
                   .limit(6).execute().data
   ```
   Los últimos 6 mensajes del chat del usuario, invertidos cronológicamente para dar contexto conversacional al LLM.

3. **Llama a `ask_llm()`** en `backend/app/services/llm.py`.

4. **Interpreta el JSON retornado** y construye una respuesta amigable según la intención detectada:

| Intención LLM | Acción del backend |
|---|---|
| `saludo` | Retorna `mensaje_libre` del LLM o un saludo genérico de AJE |
| `consulta_catalogo` | Llama a `_build_product_menu()` (lista real desde DB) |
| `fuera_de_alcance` | Retorna el `mensaje_libre` del LLM (o mensaje hardcoded según `motivo_rechazo`) |
| `pedido` | Valida cada SKU sugerido contra la DB y construye un listado de confirmación |

### 5.2 Validación de SKUs sugeridos por el LLM

El LLM propone nombres de productos, pero **el backend nunca los acepta a ciegas**:

```python
for item in llm_products:
    sku_sugerido = item.get("sku_sugerido")
    matched_product = None
    if sku_sugerido:
        for pname, prod in product_map.items():
            if sku_sugerido.lower() in pname or pname in sku_sugerido.lower():
                matched_product = prod
                break

    if matched_product:
        # ✅ Producto encontrado en catálogo real
        lines.append(f"✅ *{nombre}* → **{matched_product['name']}** x{cantidad} — Bs {precio} c/u")
    else:
        # ❓ El LLM propuso algo que no está en la DB
        lines.append(f"❓ *{nombre}* — No encontré ese producto exacto. Escribe 'menu' para ver los disponibles.")
```

---

## 6. Filtros de Seguridad y Reglas de Negocio

### 6.1 Filtro de Alcohol

**Donde se aplica:**
- **Capa 1 (NLP):** `ALCOHOL_KEYWORDS` en `nlp.py` línea 40
- **Capa 2 (LLM):** System prompt explícito + few-shot examples en `assistant_prompt.py`

**Keywords que activan el rechazo:**
```python
ALCOHOL_KEYWORDS = {
    "cheba", "cerveza", "birra", "chela", "vino", "whisky", "ron", "vodka", "licor"
}
```

**Respuesta generada:**
```
❌ Lamento informarte que no distribuimos bebidas alcohólicas.
```

**Comportamiento del LLM ante alcohol:**
El LLM retorna:
```json
{
  "intencion": "fuera_de_alcance",
  "motivo_rechazo": "alcohol",
  "mensaje_libre": "Lamento informarte que no contamos con distribución de bebidas alcohólicas como la cheba."
}
```

### 6.2 Filtro de Comida Sólida

**Donde se aplica:**
- **Capa 1 (NLP):** `SOLID_KEYWORDS` en `nlp.py` línea 36
- **Capa 2 (LLM):** System prompt explícito + few-shot examples

**Keywords que activan el rechazo:**
```python
SOLID_KEYWORDS = {
    "papas", "papitas", "papas fritas", "nachos", "galletas", "dulce",
    "hamburguesa", "pizza", "sandwich", "bocadillo", "comida", "alimento",
    "snack", "papas chips"
}
```

**Respuesta generada:**
```
❌ Lamento informarte que no contamos con ese producto, ya que nos
especializamos exclusivamente en el abastecimiento de productos líquidos y bebidas.
```

### 6.3 Filtro de Confirmación Obligatoria (Human-in-the-Loop)

**Regla crítica de negocio:** Ningún pedido se transmite a AJE sin confirmación explícita del preventista.

El flujo es:
1. El usuario pide productos → el sistema crea un `borrador` (nunca `pendiente` directamente).
2. El borrador se muestra en la app con un resumen detallado y botones de acción.
3. El preventista confirma → el sistema ejecuta `POST /orders/{order_id}/confirm` → estado pasa a `pendiente`.

**Esto protege contra:** pedidos accidentales, interpretaciones erróneas del NLP/LLM, o mensajes mal entendidos.

### 6.4 Filtro de Mensajes Estructurados del Catálogo

```python
if _is_structured_order_message(body.message):
    return None
```

Si el mensaje empieza con `"pedido estructurado desde catalogo:"`, fue generado directamente por la UI de la app (el usuario seleccionó productos desde la pantalla de catálogo, no escribió texto libre). En este caso el sistema salta todo el pipeline conversacional y procesa directamente la estructura de datos embebida en el mensaje.

---

## 7. Sistema de Acciones Embebidas en Mensajes (`@@action`)

Las respuestas del agente pueden incluir **líneas de metadatos especiales** que la app móvil interpreta como widgets interactivos (botones, tarjetas):

```python
CHAT_ACTION_PREFIX = "@@action "

def _action_line(payload: dict) -> str:
    return f"{CHAT_ACTION_PREFIX}{json.dumps(payload)}"
```

**Tipos de acciones:**

| Tipo | Descripción | Ejemplo de payload |
|---|---|---|
| `order` | Tarjeta clickeable de un pedido | `{"type": "order", "order_id": "...", "label": "Ver pedido #a1b2", "store": "...", "status": "Pendiente", "total": "Bs 45.00", "delivery": "2026-06-07"}` |
| `orders` | Botón para ver más pedidos | `{"type": "orders", "status": "pendiente", "label": "Ver más pedidos pendientes"}` |
| `message` | Botón de acceso rápido que envía un mensaje predefinido | `{"type": "message", "message": "Menu", "label": "Ver menu"}` |

La app móvil renderiza estas líneas como tarjetas visuales en lugar de texto plano.

---

## 8. Sistema de Feedback del Agente

Los usuarios pueden calificar las respuestas del agente con 👍 o 👎:

**Endpoint:** `POST /chat/messages/{message_id}/feedback`

**Restricción:** Solo se pueden calificar mensajes donde `sender` sea uno de:
```python
AGENT_SENDERS = {"empresa", "system", "assistant", "agent"}
```

Los votos se guardan en la tabla `agent_feedback` con:
- `rating`: `like` o `dislike`
- `comment`: comentario opcional
- `context`: snapshot del mensaje y sender en el momento del voto

**Uso previsto:** Revisar los `dislike` semanalmente para identificar frases que el agente interpretó mal y agregarlas al dataset de entrenamiento (`cochabamba_cercado_orders.json`) o como nuevos aliases en la base de datos.

---

## 9. ✅ Qué Funciona Bien

| Funcionalidad | Estado | Notas |
|---|---|---|
| Pedidos estándar con cantidad y producto | ✅ Funciona | `"dame 3 big cola 2L"` → borrador creado |
| Jerga boliviana registrada | ✅ Funciona | `cielito`, `voltcito`, `orito`, `coquita` → mapeados a SKUs |
| Typos comunes de preventistas | ✅ Funciona | `sielo`, `cifru`, `votl`, `bigg` → corregidos antes del fuzzy |
| Fuzzy matching (errores leves) | ✅ Funciona | `"agua ciello"` → matchea `Agua Cielo` con score ~85 |
| Menú/catálogo dinámico | ✅ Funciona | Lista real de productos activos desde DB en tiempo real |
| Lista y filtro de pedidos | ✅ Funciona | Filtra por cualquier estado con sus aliases |
| Consulta de estado de pedido | ✅ Funciona | Muestra estado, tienda, fecha y total |
| Confirmación de borradores | ✅ Funciona | Palabras naturales de confirmación activan el envío |
| Rechazo de alcohol | ✅ Funciona | Detectado en Capa 1 y Capa 2 con mensaje explicativo |
| Rechazo de comida sólida | ✅ Funciona | Detectado en Capa 1 y Capa 2 con mensaje explicativo |
| Saludo y respuesta conversacional | ✅ Funciona vía LLM | El NLP de reglas no maneja saludos; los toma el LLM |
| Pedidos multi-producto | ✅ Funciona | `"3 volt y 2 cielo"` → detecta ambos productos |
| Correcciones: "no quiero X, solo Y" | ✅ Funciona | Extrae la parte después de "solo" y reintenta |
| Preguntas libres ("qué tienes fresco?") | ✅ Funciona vía LLM | Clasifica como `consulta_catalogo` y muestra menú |
| Sistema de feedback (like/dislike) | ✅ Funciona | Persiste en `agent_feedback` |
| Acciones embebidas (tarjetas/botones) | ✅ Funciona | La app renderiza `@@action` como widgets |
| Warmup automático del LLM al inicio | ✅ Funciona | Evita cold-start de 30s en la primera petición |

---

## 10. ❌ Qué NO Funciona y Por Qué

### 10.1 El LLM no crea pedidos directamente

**Problema:** Cuando el LLM detecta un `pedido`, el backend muestra al usuario los productos encontrados con `✅`/`❓` y pregunta `"¿Confirmamos el pedido con estos productos?"`, **pero NO crea el borrador automáticamente**.

**Por qué:** La función `_llm_fallback_reply()` está diseñada solo para **interpretar** el mensaje y mostrar un resumen. No llama a `draft_order_chat_reply()` para crear el borrador en la DB. Si el usuario responde "sí", el sistema envía ese nuevo mensaje por el pipeline, pero el contexto del pedido anterior puede haberse perdido.

**Impacto:** El usuario tiene que especificar el pedido nuevamente desde cero o usar la pantalla de catálogo para pedidos complejos si el NLP de reglas no pudo procesarlo.

### 10.2 Mensajes demasiado ambiguos o cortos

**Problema:** Mensajes como `"manda"`, `"una"`, `"algo fresco"`, `"lo de siempre"` sin contexto son imposibles de resolver por la Capa 1 y difíciles de contextualizar para la Capa 2.

**Por qué:** La Capa 1 busca keywords específicas y la Capa 2 necesita al menos un nombre o descripción de producto para sugerir un SKU del catálogo. Sin esa señal, el LLM puede clasificar el mensaje como `consulta_catalogo` y mostrar el menú (que puede no ser lo que el usuario quería).

### 10.3 Jerga nueva no registrada en aliases

**Problema:** Si un preventista usa una palabra de argot local que no está ni en `TYPO_REPLACEMENTS` ni en los aliases de la base de datos y supera la distancia de Fuzzy Match (score < 70), la Capa 1 no logrará identificar el producto.

**Ejemplo:** `"una yosca"` (si fuera una jerga local para "Agua Cielo") no matchearía porque no está en ningún alias registrado. La Capa 2 (LLM) tiene más chances de interpretarlo si el LLM lo asocia semánticamente, pero no está garantizado.

**Por qué:** El fuzzy matching tiene un umbral mínimo (`CONFIRM_SCORE = 70`). Palabras demasiado distintas del nombre oficial quedan por debajo del umbral y se descartan.

### 10.4 Alta latencia del LLM en CPU sin GPU

**Problema:** Si el servidor donde corre Ollama no tiene GPU con soporte CUDA, el modelo `aje-preventista` (4.9 GB en Q4_K_M) se ejecuta en CPU. Una sola inferencia puede tomar entre 12 y 25 segundos.

**Por qué:** El modelo LLaMA 3.1 8B necesita hacer ~8 billones de operaciones de punto flotante por inferencia. En una GPU moderna esas operaciones se paralelizan masivamente (miles de núcleos CUDA). En CPU se ejecutan secuencialmente con decenas de núcleos, siendo ~10-20x más lento.

**Impacto:** El usuario espera más de 10 segundos para recibir una respuesta del agente. En la app móvil esto puede interpretarse como un error de red o "la app se colgó".

### 10.5 Concurrencia limitada del servidor Ollama

**Problema:** Ollama procesa inferencias en cola (una a la vez por defecto). Si múltiples preventistas envían mensajes que llegan a la Capa 2 simultáneamente, los mensajes posteriores esperan a que termine el primero.

**Por qué:** Los modelos GGUF en Ollama no están diseñados para inferencia paralela masiva. Para servir múltiples usuarios concurrentes de forma eficiente se necesita un sistema de batching o múltiples instancias del servidor Ollama (que requiere múltiples GPUs).

### 10.6 El LLM no persiste contexto entre sesiones

**Problema:** El LLM recibe los últimos 6 mensajes como contexto. Si una conversación tiene más de 6 turnos relevantes o el usuario se fue y volvió al día siguiente, el LLM no recuerda nada de lo anterior más allá de esos 6 mensajes.

**Por qué:** Por diseño y limitación del `context window`. Enviar toda la historia sería costoso en tokens y añadiría latencia significativa.

### 10.7 Validación de SKU del LLM es solo por substring

```python
if sku_sugerido.lower() in pname or pname in sku_sugerido.lower():
    matched_product = prod
```

**Problema:** Si el LLM sugiere `"Big Cola"` pero el catálogo tiene `"Big Cola 2L"`, `"Big Cola 3L"` y `"Big Cola 500ml"`, la primera que encuentre en el iterador será la seleccionada (no necesariamente la que el usuario quería).

**Por qué:** La validación hace substring matching simple, no considera la presentación/tamaño. No hay desambiguación posterior si hay múltiples productos que contienen el string del LLM.

---

## 11. Diagrama de Flujo Completo del Mensaje

```
POST /chat/message
      │
      ▼ Guarda el mensaje del usuario en chat_messages
      │
      ├─ sender != "user"? → No hay reply del agente. Termina.
      │
      ▼ sender == "user"
      │
      ├─ _build_chat_reply()
      │   ├─ ¿Es mensaje del catálogo estructurado?     → None (bypass)
      │   ├─ ¿Es negación pura?                         → Respuesta amable
      │   ├─ ¿Hay borrador + confirmación?              → Confirma pedido
      │   ├─ ¿Comando de finalización?                  → Confirma pedido
      │   ├─ ¿Contiene "menu/catalogo/productos"?       → Muestra catálogo
      │   ├─ ¿Contiene "estado/seguimiento/como va"?    → Estado del pedido
      │   ├─ ¿Contiene "lista/ordenes"?                 → Lista de pedidos
      │   ├─ ¿Hay filtro de estado?                     → Lista filtrada
      │   ├─ ¿Patrón "no quiero X, solo Y"?             → Redirect a NLP
      │   ├─ draft_order_chat_reply() → NLP de reglas
      │   │   ├─ ¿Es negación pura NLP?                 → Mensaje de cierre
      │   │   ├─ ¿Patrón "solo X"?                      → Procesa solo X
      │   │   ├─ ¿Hay aclaración pendiente activa?      → Resuelve aclaración
      │   │   ├─ ¿Hay borrador activo?                  → Agrega ítems al borrador
      │   │   ├─ ¿Corrección contextual?                → Reinterpreta con contexto
      │   │   ├─ ¿Parece pedido directo?                → Fuzzy match → crea borrador
      │   │   └─ Nada coincide                          → Retorna None
      │   ├─ ¿Segunda verificación confirmación?        → Confirma pedido
      │   ├─ ¿Contiene "pedido/pedidos"?                → Lista de pedidos
      │   └─ Nada coincide                              → Retorna None
      │
      ├─ reply == None? → _llm_fallback_reply()
      │   ├─ Carga catálogo activo de DB
      │   ├─ Carga últimos 6 mensajes como historial
      │   ├─ Llama ask_llm() → Ollama (aje-preventista)
      │   │   ├─ Respuesta no es JSON?   → Retry con reminder
      │   │   └─ Segundo fallo           → Retorna None
      │   ├─ intencion == "saludo"        → Mensaje de bienvenida
      │   ├─ intencion == "consulta_catalogo" → Muestra catálogo
      │   ├─ intencion == "fuera_de_alcance" → Mensaje de rechazo
      │   ├─ intencion == "pedido"        → Valida SKUs contra DB → Listado
      │   └─ Ollama no disponible         → Retorna None
      │
      └─ reply aún == None? → Mensaje hardcoded de ayuda
            "Puedo ayudarte con: menú, estado del pedido, lista de pedidos..."
      │
      ▼ Si hay reply: guarda en chat_messages con sender="empresa"
      │
      ▼ Retorna el mensaje original del usuario como ChatMessageOut
```

---

## 12. Resumen de Archivos Clave

| Archivo | Rol |
|---|---|
| `backend/app/routes/chat.py` | Orquestador principal: 3 capas, filtros, confirmaciones, acciones |
| `backend/app/routes/nlp.py` | Motor NLP de reglas: fuzzy matching, extracción de cantidades/presentaciones/fechas |
| `backend/app/services/llm.py` | Servicio LLM: comunicación con Ollama, system prompt, retry de JSON |
| `backend/assistant_prompt.py` | Few-shot examples bolivianos + mensajes de rechazo predefinidos |
| `backend/app/nlp_dataset/cochabamba_cercado_orders.json` | Dataset de entrenamiento del LLM (74 ejemplos de frases reales) |
| `backend/scratch/train_llm_model.py` | Script de entrenamiento por épocas con Ollama Modelfile |
| `backend/scratch/test_llm_fallback.py` | Suite de 13 pruebas del fallback LLM |
| `backend/.env` | Configuración: `OLLAMA_MODEL`, `LLM_FALLBACK_ENABLED`, `OLLAMA_TIMEOUT` |
