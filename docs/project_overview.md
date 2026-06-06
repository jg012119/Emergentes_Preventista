# Preventista Inteligente AJE — Documentación Técnica Completa

> **Proyecto:** Emergentes Preventista  
> **Empresa:** AJE Bolivia  
> **Grupo:** 315 WHISPER  
> **Integrantes:** Luz Laredo · Jairo Guzmán · Valentina Trigo  
> **Stakeholder:** Ing. Claudia Ureña Hinojosa  
> **Última actualización:** Junio 2026

---

## Tabla de contenidos

1. [Visión general del sistema](#1-visión-general-del-sistema)
2. [Arquitectura global](#2-arquitectura-global)
3. [Backend — FastAPI](#3-backend--fastapi)
   - [Stack y dependencias](#31-stack-y-dependencias)
   - [Configuración y entorno](#32-configuración-y-entorno)
   - [Base de datos (Supabase / SQLite)](#33-base-de-datos-supabase--sqlite)
   - [Autenticación JWT](#34-autenticación-jwt)
   - [Módulo de Pedidos](#35-módulo-de-pedidos)
   - [Motor NLP rule-based](#36-motor-nlp-rule-based)
   - [Pipeline de Chat](#37-pipeline-de-chat)
   - [Integración LLaMA (Ollama)](#38-integración-llama-ollama)
   - [Servicio de Notificaciones](#39-servicio-de-notificaciones)
   - [Reportes y métricas](#310-reportes-y-métricas)
4. [App móvil — React Native (Expo)](#4-app-móvil--react-native-expo)
   - [Navegación](#41-navegación)
   - [Pantallas](#42-pantallas)
   - [ChatScreen — la pantalla central](#43-chatscreen--la-pantalla-central)
   - [Reconocimiento de voz](#44-reconocimiento-de-voz)
   - [Manejo de estado y AsyncStorage](#45-manejo-de-estado-y-asyncstorage)
5. [Panel Web — React + Vite](#5-panel-web--react--vite)
   - [Páginas](#51-páginas)
6. [Flujos completos de usuario](#6-flujos-completos-de-usuario)
7. [Puntos críticos del sistema](#7-puntos-críticos-del-sistema)
8. [Variables de entorno](#8-variables-de-entorno)
9. [Cómo correr el proyecto](#9-cómo-correr-el-proyecto)
10. [Estructura del repositorio](#10-estructura-del-repositorio)

---

## 1. Visión general del sistema

El **Preventista Inteligente AJE** es un MVP que permite a tiendas, supermercados y mayoristas realizar pedidos de productos de bebidas AJE Bolivia usando **lenguaje natural escrito o por voz**, sin necesidad de formularios ni llamadas manuales.

### El problema que resuelve

Antes del sistema, los pedidos se hacían por WhatsApp, llamadas o notas informales, generando:
- Pedidos incompletos o con errores de cantidad
- Sin confirmación formal ni trazabilidad
- Sin validación de stock ni precios
- Dependencia total de un vendedor humano para registrar cada solicitud

### Cómo funciona a alto nivel

```
Preventista escribe/dicta:
"mándame 4 big cola 2L y 2 agüitas para mañana"
         │
         ▼
App móvil (React Native)
  → Voz convertida a texto (expo-speech-recognition, es-BO)
  → Texto enviado al backend via POST /chat/message
         │
         ▼
Backend FastAPI
  Capa 1: NLP rule-based (rapidfuzz + regex, <100ms)
  Capa 2: LLaMA 3.1 8B via Ollama (fallback, ~1-3s con GPU)
  Capa 3: Respuesta genérica hardcoded (último recurso)
         │
         ▼
Pedido borrador creado → Preview en chat → Confirmación manual
         │
         ▼
Pedido en estado PENDIENTE → Notificación chat + correo
         │
         ▼
Panel web AJE → Cambio de estado → Nueva notificación al cliente
```

---

## 2. Arquitectura global

```
┌────────────────────────────────────────────────────────────┐
│              App Móvil (React Native + Expo)                │
│   Screens: Login · Chat · Pedidos · Sucursales · Perfil    │
│   Voice: expo-speech-recognition (lang: es-BO)             │
└──────────────────────┬─────────────────────────────────────┘
                       │ HTTPS / JSON  (Bearer JWT)
                       │ EXPO_PUBLIC_API_URL  (port 8000)
┌──────────────────────▼─────────────────────────────────────┐
│                  Backend FastAPI (Python)                    │
│  /auth  /users  /stores  /products  /orders  /chat  /nlp   │
│  /reports  /notifications                                   │
│                                                             │
│  Capas de procesamiento de lenguaje:                        │
│  1. NLP Rule-based  (nlp.py · rapidfuzz · dateparser)       │
│  2. LLM Fallback    (llm.py · Ollama · llama3.1:8b)         │
│  3. Hardcoded reply (último recurso)                        │
│                                                             │
│  Notification Service (SMTP Gmail + chat_messages)          │
└──────┬────────────────────────────┬────────────────────────┘
       │ supabase-py (service key)  │ httpx → localhost:11434
┌──────▼──────────────┐   ┌─────────▼───────────────────────┐
│  Supabase           │   │  Ollama (local)                  │
│  (PostgreSQL cloud) │   │  llama3.1:8b / aje-preventista   │
│  Fallback: SQLite   │   └──────────────────────────────────┘
│  (local.db)         │
└──────────────────────┘
         ▲
         │  HTTPS / JSON  (Bearer JWT)
┌────────┴────────────────────────────────────────────────────┐
│              Panel Web AJE (React + Vite)                   │
│  Pages: Login · Dashboard · Orders · Products · Reports     │
│         Clients · OrderDetail · Profile                     │
└─────────────────────────────────────────────────────────────┘
```

### Decisión de base de datos dual

`config.py` detecta automáticamente si las credenciales de Supabase son válidas:
- **Con credenciales válidas** → usa Supabase (PostgreSQL en la nube)
- **Sin credenciales / inválidas** → usa SQLite local (`backend/local.db`)

Esto permite desarrollar sin internet ni cuenta Supabase.

---

## 3. Backend — FastAPI

### 3.1 Stack y dependencias

| Librería | Versión | Uso |
|---|---|---|
| `fastapi` | 0.115.0 | Framework HTTP |
| `uvicorn[standard]` | 0.30.0 | Servidor ASGI |
| `supabase` | 2.9.1 | Cliente de base de datos |
| `python-jose[cryptography]` | 3.3.0 | JWT (HS256) |
| `passlib[bcrypt]` | 1.7.4 | Hashing de contraseñas |
| `pydantic[email]` | ≥2.13.4 | Validación de schemas |
| `httpx` | 0.27.0 | Cliente HTTP async (Ollama) |
| `dateparser` | 1.2.0 | Parseo de fechas en lenguaje natural |
| `rapidfuzz` | 3.9.0 | Fuzzy matching para NLP |
| `python-dotenv` | 1.0.1 | Variables de entorno |

### 3.2 Configuración y entorno

**Archivo:** `backend/app/config.py`

```python
# Lógica de selección automática de DB
_USE_LOCAL_DB = (
    not SUPABASE_URL
    or any(marker in SUPABASE_URL for marker in _PLACEHOLDER_MARKERS)
    or not _is_valid_supabase_key(SUPABASE_KEY)  # acepta JWT y nuevo formato sb_*
)
```

Acepta dos formatos de key de Supabase:
- Formato JWT clásico: `eyJxxx.eyJxxx.xxx`
- Formato nuevo: `sb_publishable_xxx` / `sb_secret_xxx`

**Archivo:** `backend/.env`

```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=sb_publishable_...
SUPABASE_SERVICE_KEY=eyJ...
JWT_SECRET=AJE_Preventista_Super_Secret_2026_Secure_Key!
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440   # 24 horas
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=aje95341@gmail.com
EMAIL_PASSWORD=...

# LLM Fallback
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
OLLAMA_TIMEOUT=30
LLM_FALLBACK_ENABLED=true
```

### 3.3 Base de datos (Supabase / SQLite)

#### Tablas principales

| Tabla | Campos clave | Descripción |
|---|---|---|
| `users` | `id (UUID)`, `name`, `email`, `phone`, `password_hash` | Preventistas / clientes |
| `stores` | `id`, `user_id`, `name`, `address`, `latitude`, `longitude` | Tiendas registradas |
| `products` | `id`, `name`, `category`, `price`, `stock`, `active` | Catálogo AJE |
| `orders` | `id`, `user_id`, `store_id`, `status`, `delivery_date`, `total`, `nlp_data` | Pedidos |
| `order_items` | `id`, `order_id`, `product_id`, `quantity`, `unit_price`, `subtotal` | Detalle de cada pedido |
| `chat_messages` | `id`, `user_id`, `order_id`, `message`, `sender`, `feedback_rating` | Historial de chat |
| `notifications` | `id`, `user_id`, `order_id`, `type`, `message`, `status` | Log de notificaciones |
| `chat_feedback` | `id`, `user_id`, `message_id`, `rating`, `comment` | Feedback (👍/👎) de respuestas |

#### Campo especial `nlp_data`

El campo `orders.nlp_data` (JSON) guarda la extracción cruda del NLP para auditoría:
```json
{
  "intent": "pedido",
  "confidence_score": 0.92,
  "raw_text": "mándame 4 big cola 2L",
  "items": [{"raw_text": "4 big cola 2L", "cantidad": 4, ...}]
}
```

#### Estados del pedido

```
borrador → pendiente → confirmado → en_proceso → pagado
                    ↘ rechazado
```

> ⚠️ **Punto crítico:** El stock **se descuenta** al confirmar el pedido (estado `pendiente`), y **se restituye** si AJE lo rechaza. Esto puede generar race conditions si dos confirmaciones ocurren simultáneamente.

### 3.4 Autenticación JWT

**Archivo:** `backend/app/utils/auth.py`

- **Algoritmo:** HS256 con `JWT_SECRET`
- **Expiración:** 1440 minutos (24 horas)
- **Claim:** `sub` = `user_id` (UUID de Supabase)
- **Dependency FastAPI:** `get_current_user_id` — se inyecta en todos los endpoints protegidos

```python
# Uso en rutas
@router.get("/me")
async def get_me(user_id: str = Depends(get_current_user_id)):
    ...
```

> ⚠️ **Punto crítico:** No existe sistema de roles. El panel AJE usa el mismo JWT que la app móvil. Cualquier usuario autenticado puede llamar a `/orders/all` (endpoint "admin") o cambiar el estado de cualquier pedido. Esto es una vulnerabilidad de autorización pendiente de resolver.

### 3.5 Módulo de Pedidos

**Archivo:** `backend/app/routes/orders.py`

#### Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/orders/draft` | Crea pedido en estado `borrador` |
| `PUT` | `/orders/{id}/draft` | Actualiza pedido borrador |
| `POST` | `/orders/{id}/confirm` | Confirma borrador → `pendiente` + descuenta stock |
| `GET` | `/orders/` | Lista pedidos del usuario autenticado |
| `GET` | `/orders/all` | Lista TODOS los pedidos (panel AJE) |
| `GET` | `/orders/{id}` | Detalle de un pedido |
| `PUT` | `/orders/{id}/status` | Cambia estado + notifica (AJE) |
| `PUT` | `/orders/{id}/delivery-date` | Cambia fecha de entrega (máx. 7 días) |

#### Flujo de confirmación (`confirm_order_in_db`)

```python
# 1. Verificar que el pedido es borrador
# 2. Revalidar stock de cada item
# 3. Descontar stock de cada producto
# 4. Cambiar status a "pendiente"
# 5. Insertar chat_message de confirmación
```

> ⚠️ **Punto crítico:** `_enrich_order()` hace **N+1 queries** (una por producto en `order_items` para obtener el nombre). En pedidos con muchos items o bajo alta carga, esto es lento. Debería hacerse con un JOIN o una sola query con todos los IDs.

### 3.6 Motor NLP rule-based

**Archivo:** `backend/app/routes/nlp.py` (~2364 líneas)

Este es el componente más complejo del sistema. Procesa texto en español boliviano coloquial y extrae pedidos estructurados.

#### Pipeline de extracción

```
Texto crudo
    │
    ▼
_normalize_text()        → Unicode NFKD, lowercase, trim
    │
    ▼
_detect_intent()         → pedido / saludo / menu / consulta
    │
    ▼
_strip_date_tail()       → extrae "para mañana", "el viernes", etc.
    │
    ▼
_parse_date()            → dateparser + lógica propia (hoy/mañana/pasado mañana)
    │
    ▼
SPLIT_RE.split()         → separa ítems por "," "y" "+" ";" "también"
    │
    ▼  (por cada ítem)
_parse_item_text()
    ├── _extract_quantity()     → números + palabras (un/dos/tres/docena)
    ├── _extract_presentation() → 500ml / 1L / 2.5L / etc.
    ├── _extract_unit()         → caja / lata / six / pack
    └── _match_product()        → fuzzy matching contra catálogo DB
           ├── rapidfuzz.fuzz.partial_ratio()
           ├── _check_aliases()         → aliases de la tabla DB
           ├── _matched_name_contains_variant()  → variantes de nombre
           └── Score > AUTO_ACCEPT_SCORE (90) → match automático
               Score 70-90 → requiere clarificación
               Score < 70  → sin match
    │
    ▼
NLPParseOrderResponse     → items + fecha + confidence + clarification_questions
```

#### Constantes de umbral de confianza

| Constante | Valor | Significado |
|---|---|---|
| `AUTO_ACCEPT_SCORE` | 90 | Match automático sin preguntar |
| `CONFIRM_SCORE` | 70 | Requiere confirmación del usuario |
| `AMBIGUOUS_GAP` | 5 | Diferencia mínima entre candidatos para no pedir aclaración |

#### Vocabulario boliviano embebido

```python
QUANTITY_WORDS = {"un": 1, "una": 1, "dos": 2, ..., "docena": 12}

SOLID_KEYWORDS = {"papas", "papitas", "nachos", "hamburguesa", "pizza", ...}
ALCOHOL_KEYWORDS = {"cheba", "cerveza", "birra", "chela", "vino", ...}

FILLER_RE   → quiero / dame / manda / mandame / anotame / pasame / llevame...
ORDER_INTENT_RE → quiero / necesito / dame / pa / para...
```

#### Manejo de contexto conversacional

El NLP soporta pedidos multi-turno. La clave `context.pending_order_text` llega desde el frontend:

```python
# Si el usuario dice "dame 2 big" luego "y también 3 cielos"
# El frontend acumula el texto completo y lo envía como contexto
context = {
    "active_order_id": "uuid-del-borrador",
    "pending_order_text": "dame 2 big también 3 cielos"
}
```

> ⚠️ **Punto crítico (bug conocido):** En la función `_matched_name_contains_variant()` existe código inalcanzable después de un `return`. No afecta la funcionalidad pero es un indicio de lógica incompleta en esa rama de matching.

#### Endpoints NLP

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/nlp/parse` | Parse rápido (sin draft) |
| `POST` | `/nlp/parse-order` | Parse + crea borrador si hay match completo |
| `POST` | `/nlp/validate` | Valida stock/precios de una extracción |
| `POST` | `/nlp/correct` | Registra corrección manual del usuario |
| `GET` | `/nlp/llm-status` | Estado de Ollama |

### 3.7 Pipeline de Chat

**Archivo:** `backend/app/routes/chat.py` (650 líneas)

El chat es la interfaz principal del sistema. Cada mensaje del usuario pasa por este pipeline:

```python
POST /chat/message
{
  "message": "dame 3 volta 300",
  "order_id": null,          # null = chat general
  "context": {
    "active_order_id": "uuid",
    "pending_order_text": "..."
  }
}
```

#### Árbol de decisión del pipeline

```
_build_chat_reply(db, user_id, body)
    │
    ├── Es saludo? → respuesta de bienvenida
    │
    ├── Es "menu"/"catálogo"? → _build_product_menu()
    │
    ├── Es consulta de pedidos? ("mis pedidos pendientes") → lista + @@action
    │
    ├── Es confirmación? ("si", "dale", "confirmar") + hay borrador activo
    │       → confirm_order_in_db()
    │
    ├── Es negación pura? ("no gracias") → respuesta neutral
    │
    ├── Tiene contexto de borrador activo + mensaje contextual?
    │       → agrega items al borrador existente
    │
    └── Intenta NLP completo → draft_order_chat_reply()
            │
            ¿NLP retornó None?
            │
            └── LLM Fallback → _llm_fallback_reply()
                    │
                    ¿LLM retornó None?
                    │
                    └── Respuesta genérica hardcoded
```

#### Protocolo `@@action`

El backend embebe acciones ejecutables en los mensajes de chat usando el prefijo `@@action`:

```
Tu pedido borrador #abc12345 fue creado.
Tienda: Tienda San Miguel
...
@@action {"type":"confirm_order","order_id":"uuid","label":"Confirmar y enviar a AJE"}
```

La app móvil parsea estas líneas y las renderiza como botones interactivos. Tipos de acción:

| Tipo | Descripción |
|---|---|
| `confirm_order` | Botón para confirmar el borrador |
| `order` | Enlace a detalle de un pedido |
| `orders` | Enlace a lista de pedidos filtrada |
| `message` | Envía un mensaje predefinido |

#### Feedback de respuestas

Cada respuesta del agente permite thumbs up/down:
```
POST /chat/messages/{message_id}/feedback
{"rating": "like" | "dislike", "comment": "..."}
```

Guardado en tabla `chat_feedback` para análisis y mejora del sistema.

### 3.8 Integración LLaMA (Ollama)

**Archivo:** `backend/app/services/llm.py`

Activado solo cuando el NLP rule-based retorna `None`.

#### Función `warmup()`

```python
# Se llama al arrancar FastAPI (lifespan)
# Pre-carga el modelo en GPU/RAM
# Evita timeout de cold-start en la primera petición real
# Timeout extendido: 60 segundos
```

#### Función `ask_llm()`

```python
# temperatura: 0.05 (muy determinista para JSON consistente)
# num_predict: 512 tokens máximo
# Retry automático: si la respuesta no es JSON válido, reintenta
#   una vez con un "reminder" fuerte en el prompt
# Retorna: dict | None (nunca lanza excepción)
```

#### System prompt inyectado

El catálogo **real de la DB** se inyecta en cada llamada al LLM:
```
Catálogo disponible (SOLO estos productos existen):
- Big Cola 2L  Bs 10.00  stock: 50
- Agua Cielo 500ml  Bs 2.00  stock: 150
...
```

Esto garantiza que el LLM solo sugiera SKUs que existen.

#### Entrenamiento con épocas

**Archivo:** `backend/scratch/train_llm_model.py`

Usa Ollama Modelfile para bake-in ejemplos del dataset como few-shot learning:

```
Época 1: 30% dataset (≈16 ejemplos) → aje-preventista-e1
Época 2: 60% dataset (≈32 ejemplos) → aje-preventista-e2
Época 3: 100% dataset (≈54 ejemplos) → aje-preventista-e3
→ Selecciona mejor época por score compuesto
→ Crea modelo final: aje-preventista
```

**Dataset:** `backend/app/nlp_dataset/cochabamba_cercado_orders.json` — 74 ejemplos de pedidos reales en lenguaje coloquial boliviano.

### 3.9 Servicio de Notificaciones

**Archivo:** `backend/app/services/notification_service.py`

Se activa al cambiar el estado de un pedido:

```python
async def notify_status_change(db, order, new_status):
    # 1. Construye resumen del pedido con items
    # 2. Inserta mensaje en chat_messages (sender="system")
    # 3. Inserta registro en notifications
    # 4. Intenta enviar email SMTP (Gmail con App Password)
    #    → Si falla: registra "fallido" en notifications pero NO lanza excepción
```

**Email HTML generado:**
```html
<h2 style="color: #1a73e8;">Preventista Inteligente — AJE</h2>
<p>Hola <strong>nombre</strong>,</p>
<pre>Tu pedido #abc12345 fue confirmado por AJE. ...</pre>
```

> ⚠️ **Punto crítico:** El email usa SMTP directo con `smtplib`. Si el servidor de AJE Google bloquea el App Password o hay problemas de red, el email falla silenciosamente. Considerar usar un servicio como SendGrid o Resend para producción.

### 3.10 Reportes y métricas

**Archivo:** `backend/app/routes/reports.py`

Endpoint `GET /reports/agent` retorna:

```json
{
  "summary": {
    "orders_taken": 42,
    "orders_with_agent": 38,
    "auto_messages": 156,
    "agent_share": 78.0,
    "customers_touched": 12,
    "avg_messages_per_order": 3.7
  },
  "closing": {
    "close_rate": 85.2,
    "confirmed_orders": 29,
    "rejected_orders": 5
  },
  "values": {
    "total_value": 4850.50,
    "confirmed_value": 3920.00,
    "pipeline_value": 520.00
  },
  "timeline": [...],       // últimos 14 días
  "top_clients": [...],    // top 5 por valor
  "top_stores": [...],     // top 5 por valor
  "top_products": [...]    // top 6 por cantidad
}
```

> ⚠️ **Punto crítico:** El endpoint carga **todas** las tablas en memoria para hacer los cálculos en Python. Con volumen alto de datos (miles de pedidos), esto es un problema de rendimiento. Debería usar agregaciones SQL en Supabase.

---

## 4. App Móvil — React Native (Expo)

### 4.1 Navegación

```
NavigationContainer
└── Stack.Navigator
    ├── [no token] Login → Register
    └── [con token]
        ├── Main (Bottom Tabs)
        │   ├── Chat (tab inicial)
        │   ├── Pedidos
        │   ├── Sucursales
        │   └── Perfil
        ├── CreateStore
        ├── Catalog
        ├── CreateOrder
        ├── OrderConfirm
        ├── OrderDetail
        └── OrderChat (ChatScreen con orderId)
```

El token JWT se persiste en `AsyncStorage` bajo la clave `'token'`. Al arrancar la app, se lee y se inyecta en todas las llamadas API.

### 4.2 Pantallas

| Pantalla | Archivo | Descripción |
|---|---|---|
| `LoginScreen` | login | Formulario email/password → `POST /auth/login` |
| `RegisterScreen` | register | Registro nuevo preventista |
| `ChatScreen` | chat | **Pantalla principal** — chat con el agente |
| `OrdersScreen` | orders | Lista de pedidos del usuario con filtros |
| `OrderDetailScreen` | order-detail | Detalle de pedido + historial chat |
| `StoresScreen` | stores | Lista de sucursales registradas |
| `CreateStoreScreen` | create-store | Registro de nueva sucursal + mapa |
| `ProfileScreen` | profile | Perfil del usuario + logout |
| `CatalogScreen` | catalog | Catálogo visual de productos con botones |
| `CreateOrderScreen` | create-order | Formulario manual de pedido |
| `OrderConfirmScreen` | order-confirm | Pantalla de confirmación antes de enviar |

### 4.3 ChatScreen — la pantalla central

**Archivo:** `mobile/src/screens/ChatScreen.js` (1156 líneas)

Es la pantalla más compleja del sistema. Tiene dos modos:
- **Chat general** (`orderId = null`) — para iniciar nuevos pedidos
- **Chat de pedido** (`orderId = uuid`) — para ver historial de un pedido específico

#### Funcionalidades clave

**Polling automático cada 5 segundos:**
```javascript
useEffect(() => {
  load();
  const interval = setInterval(load, 5000);
  return () => clearInterval(interval);
}, [load]);
```

**Optimistic UI:** El mensaje del usuario aparece inmediatamente en el chat (con ID temporal `local-${Date.now()}`) antes de que el servidor confirme.

**Parser de acciones `@@action`:**
```javascript
const parseMessageParts = (message) => {
  // Separa texto visible de líneas @@action JSON
  // Retorna { text: "...", actions: [...] }
};
```

**Gestión de contexto acumulado (`pending_order_text`):**
```javascript
// Si el usuario escribe mensajes relacionados con el pedido,
// el texto se acumula en AsyncStorage y se envía como contexto
// para que el NLP pueda combinarlos
```

**Detección de comandos para limpiar contexto:**
```javascript
const shouldClearPendingBeforeSend = (message) => {
  // "menu", "catálogo", "estado" → limpia contexto
  // Nuevo pedido fresco (quiero/dame/manda...) → también limpia
};
```

#### Heurísticas de detección de orden

```javascript
const ORDER_CONTEXT_RE = /\b(big|cielo|agua|volt|oro|pulp|cifrut|cola|lata|caja|litro|ml|mañana|hoy|\d+)\b/i;
const FRESH_ORDER_RE = /^\s*(quiero|necesito|dame|manda|mandame|mándame|...)\b/i;
const CONTEXT_APPEND_RE = /^\s*(tambien|también|ademas|y|sumale|agrega|...)\b/i;
```

### 4.4 Reconocimiento de voz

**Módulo:** `expo-speech-recognition` (require dinámico)

```javascript
await speech.start({
  lang: 'es-BO',           // Español boliviano
  interimResults: true,     // Resultados parciales mientras habla
  continuous: false,        // Para automáticamente
  addsPunctuation: true,    // Agrega puntuación
  androidIntentOptions: { EXTRA_LANGUAGE_MODEL: 'free_form' },
});
```

**Flujo de voz:**
1. Usuario toca el ícono de micrófono
2. `speech.start()` → eventos: `start` / `result` / `end` / `error`
3. Al terminar, el transcript se envía automáticamente (`autoInterpretRef = true`)
4. Si toca el micrófono de nuevo mientras graba → `speech.stop()` → envío

> ⚠️ **Punto crítico:** Si `expo-speech-recognition` no está disponible (Expo Go no lo soporta), el módulo retorna `null` y el botón de micrófono muestra un `Alert`. Requiere build de desarrollo (`expo run:android`) o build de producción.

### 4.5 Manejo de estado y AsyncStorage

| Clave AsyncStorage | Descripción |
|---|---|
| `'token'` | JWT del usuario autenticado |
| `preventista.activeDraftOrderId` | UUID del pedido borrador activo |
| `preventista.pendingOrderText.v2` | Texto acumulado del pedido en curso |

---

## 5. Panel Web — React + Vite

### 5.1 Páginas

| Página | Archivo | Descripción |
|---|---|---|
| `Login` | Login.jsx | Autenticación del operador AJE |
| `Dashboard` | Dashboard.jsx | Resumen rápido de métricas |
| `Orders` | Orders.jsx | Lista de todos los pedidos con filtros |
| `OrderDetail` | OrderDetail.jsx | Detalle + cambio de estado del pedido |
| `Products` | Products.jsx | CRUD de productos (nombre, precio, stock) |
| `Clients` | Clients.jsx | Lista de clientes/preventistas |
| `Reports` | Reports.jsx | Métricas del agente con gráficas |
| `Profile` | Profile.jsx | Perfil del operador AJE |

El panel usa `localStorage` para el token JWT (en vez de `AsyncStorage` de React Native).

```javascript
const API_URL = import.meta.env.VITE_API_URL
  || `${window.location.protocol}//${window.location.hostname}:8000`;
```

> ⚠️ **Punto crítico:** `getClients()` llama a `/users/clients` — un endpoint que **no existe** en el backend actual (solo existe `/users/me`). La página de Clients del panel fallará con 404 en producción.

---

## 6. Flujos completos de usuario

### Flujo 1: Pedido por voz (camino feliz)

```
1. Usuario abre app → accede con email/password → JWT guardado
2. Tab "Chat" → toca micrófono
3. Habla: "mándame cuatro big cola dos litros y dos agüitas para mañana"
4. expo-speech-recognition → texto → sendTextMessage()
5. POST /chat/message { message: "mándame 4 big cola 2L y 2 agüitas para mañana" }

BACKEND:
6. NLP detecta intent "pedido"
7. Extrae: [{"Big Cola 2L", qty:4}, {"Agua Cielo 500ml", qty:2}]
8. Parsea fecha: mañana = today+1
9. Valida productos contra DB → ambos encontrados con score > 90
10. Crea borrador en DB (status: "borrador")
11. Responde: "Pedido borrador #abc12345 creado.
    Tienda: ...
    @@action {type:confirm_order, order_id:'uuid', label:'Confirmar'}"

FRONTEND:
12. Chat muestra mensaje + botón "Confirmar y enviar a AJE"
13. Usuario toca "Confirmar"
14. POST /orders/uuid/confirm
    → Stock descontado
    → Status: "pendiente"
    → Chat message de confirmación
    → Email enviado al usuario

15. Panel AJE ve el pedido pendiente
16. Operador cambia status a "confirmado"
17. PUT /orders/uuid/status { status: "confirmado" }
    → notify_status_change() → chat_message + email al cliente
```

### Flujo 2: NLP falla → LLM Fallback

```
1. Usuario: "agüita fresquita la más pequeña"
2. NLP rule-based → no matchea con suficiente confianza → retorna None
3. _llm_fallback_reply() llamado
4. Carga catálogo de DB → inyecta en system prompt
5. POST http://localhost:11434/api/chat
   { model: "llama3.1:8b", messages: [...], temperature: 0.05 }
6. LLM retorna JSON:
   { "intencion": "pedido",
     "productos": [{"nombre_detectado": "agüita", "sku_sugerido": "Agua Cielo 500ml", "cantidad": 1}] }
7. Backend valida sku_sugerido contra DB real
8. Crea borrador → responde al usuario
```

### Flujo 3: Rechazo de producto fuera de catálogo

```
1. Usuario: "mándame unas chelas bien frías"
2. NLP detecta ALCOHOL_KEYWORDS → rechaza con mensaje específico
   "Lo sentimos, no distribuimos alcohol. ¿Te ayudo con algo más?"
3. NO llega al LLM (el NLP maneja el rechazo directamente)
```

---

## 7. Puntos críticos del sistema

> Esta sección documenta los problemas conocidos y las decisiones de diseño que requieren atención.

### 🔴 CRÍTICO — Seguridad

**1. Sin sistema de roles (autorización plana)**

Todos los usuarios autenticados tienen acceso a todos los endpoints. El panel AJE usa el mismo JWT que la app del preventista. Cualquier usuario puede:
- Listar todos los pedidos de todos los clientes (`GET /orders/all`)
- Cambiar el estado de cualquier pedido (`PUT /orders/{id}/status`)
- Eliminar productos (`DELETE /products/{id}`)

**Solución pendiente:** Agregar campo `role` en tabla `users` (preventista / admin) y validar en cada endpoint sensible.

---

**2. JWT_SECRET en .env del repositorio**

El secreto JWT está en el archivo `.env` que podría ser comprometido. En producción debe rotarse y cargarse desde un vault o variable de entorno del servidor.

---

### 🟠 ALTO — Rendimiento

**3. N+1 queries en `_enrich_order()`**

```python
for item in items:
    prod = db.table("products").select("name").eq("id", item["product_id"]).execute()
    # Una query por producto → lento con pedidos grandes
```

**Solución:** Cargar todos los productos de una vez con `.in_()`:
```python
product_ids = [item["product_id"] for item in items]
products = db.table("products").select("id,name").in_("id", product_ids).execute()
```

---

**4. `GET /reports/agent` carga todo en memoria**

Carga todas las tablas (orders, items, products, messages, notifications, stores, users) en Python para procesarlas. Con crecimiento de datos será muy lento.

**Solución:** Mover cálculos a SQL (Supabase RPC functions o views).

---

**5. Polling cada 5 segundos en ChatScreen**

```javascript
const interval = setInterval(load, 5000);  // Se ejecuta siempre
```

En producción con muchos usuarios, esto genera mucho tráfico al backend. 

**Solución recomendada:** Supabase Realtime (WebSockets) para recibir nuevos mensajes en tiempo real sin polling.

---

### 🟡 MEDIO — Funcionalidad

**6. Bug en `_matched_name_contains_variant()`**

Código inalcanzable después de un `return` en la función de matching de variantes de nombre. No causa errores pero indica lógica incompleta.

---

**7. `getClients()` llama a endpoint inexistente**

El panel llama a `GET /users/clients` que no está implementado en el backend. La página de clientes del panel web siempre falla con 404.

---

**8. Race condition en descuento de stock**

Si dos usuarios confirman simultáneamente un pedido del mismo producto:
1. Usuario A lee stock = 5
2. Usuario B lee stock = 5  
3. Usuario A descuenta → stock = 4
4. Usuario B descuenta sobre el stock viejo → stock = 4 (debería ser 3)

**Solución:** Usar transacción atómica en Supabase:
```sql
UPDATE products SET stock = stock - quantity WHERE id = ... AND stock >= quantity;
```

---

**9. Email falla silenciosamente**

Si el envío SMTP falla (credenciales, red, rate limit), el error se captura y se registra como "fallido" pero el usuario no recibe ninguna notificación alternativa.

---

**10. LLM cold-start en primera petición**

A pesar del `warmup()` al startup, si Ollama reinicia o el modelo se descarga de RAM, la primera petición toma 30+ segundos y hace timeout.

**Mitigación actual:** `warmup()` en lifespan + retry. Pendiente: aumentar `OLLAMA_TIMEOUT` para el primer request post-startup.

---

**11. `expo-speech-recognition` no funciona en Expo Go**

Los preventistas que usen Expo Go no tendrán reconocimiento de voz. Requiere build de desarrollo o APK firmado.

---

### 🟢 BAJO — Deuda técnica

**12. `schema.sql` está vacío**

El archivo `backend/database/schema.sql` está vacío. El schema real solo existe en Supabase. Debería exportarse y versionarse para tener un registro del estado de la DB.

**13. `nlp.py` tiene 2364 líneas**

Difícil de mantener. Debería modularizarse en:
- `nlp/intent_detector.py`
- `nlp/product_matcher.py`
- `nlp/date_extractor.py`
- `nlp/quantity_extractor.py`

**14. Sin tests automatizados del pipeline completo**

Los scripts en `scratch/` son para pruebas manuales. No hay tests unitarios del NLP rule-based integrados en un framework de testing (pytest).

---

## 8. Variables de entorno

| Variable | Requerida | Default | Descripción |
|---|---|---|---|
| `SUPABASE_URL` | ✅ | — | URL del proyecto Supabase |
| `SUPABASE_KEY` | ✅ | — | Anon key (JWT o sb_publishable) |
| `SUPABASE_SERVICE_KEY` | ✅ | — | Service role key (permisos admin) |
| `JWT_SECRET` | ✅ | `change-me` | Secreto para firmar tokens JWT |
| `JWT_ALGORITHM` | ❌ | `HS256` | Algoritmo JWT |
| `JWT_EXPIRATION_MINUTES` | ❌ | `1440` | Expiración en minutos (24h) |
| `EMAIL_HOST` | ❌ | `smtp.gmail.com` | Servidor SMTP |
| `EMAIL_PORT` | ❌ | `587` | Puerto SMTP (TLS) |
| `EMAIL_USER` | ✅ | — | Cuenta Gmail con App Password |
| `EMAIL_PASSWORD` | ✅ | — | App Password de Gmail |
| `OLLAMA_URL` | ❌ | `http://localhost:11434` | URL del servidor Ollama |
| `OLLAMA_MODEL` | ❌ | `llama3.1:8b` | Modelo LLaMA a usar |
| `OLLAMA_TIMEOUT` | ❌ | `30` | Timeout en segundos por request |
| `LLM_FALLBACK_ENABLED` | ❌ | `true` | Habilitar/deshabilitar LLM |

---

## 9. Cómo correr el proyecto

### Backend

```bash
cd backend

# 1. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
# .venv\Scripts\activate       # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# 4. Levantar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5. (Opcional) Levantar con Ollama
ollama serve &
ollama pull llama3.1:8b
uvicorn app.main:app --reload

# Documentación interactiva disponible en:
# http://localhost:8000/docs
```

### App móvil

```bash
cd mobile

# 1. Instalar dependencias
npm install

# 2. Configurar API URL
# En .env: EXPO_PUBLIC_API_URL=http://TU_IP:8000

# 3. Modo desarrollo (sin reconocimiento de voz)
npx expo start

# 4. Build con reconocimiento de voz
npx expo run:android     # o run:ios
```

### Panel web

```bash
cd panel

# 1. Instalar dependencias
npm install

# 2. Configurar API URL
# En .env: VITE_API_URL=http://TU_IP:8000

# 3. Modo desarrollo
npm run dev

# 4. Build producción
npm run build
```

### Ollama (LLM local)

```bash
# Instalar
curl -fsSL https://ollama.com/install.sh | sh

# Descargar modelo base (4.7 GB)
ollama pull llama3.1:8b

# Entrenar modelo personalizado AJE
cd backend && source .venv/bin/activate
python -m scratch.train_llm_model
# → Crea aje-preventista con 3 épocas

# Actualizar en .env:
# OLLAMA_MODEL=aje-preventista

# Verificar desde la API:
# GET http://localhost:8000/nlp/llm-status
```

---

## 10. Estructura del repositorio

```
Emergentes_Preventista/
│
├── README.md                    # Documentación general del proyecto
├── docs/
│   ├── llm_integration.md       # Doc técnico de integración LLaMA
│   └── project_overview.md      # Este documento
│
├── backend/
│   ├── .env / .env.example      # Variables de entorno
│   ├── requirements.txt         # Dependencias Python
│   ├── assistant_prompt.py      # Few-shots bolivianos para LLM
│   ├── local.db                 # SQLite de desarrollo (fallback)
│   └── app/
│       ├── main.py              # Entrypoint FastAPI + lifespan warmup
│       ├── config.py            # Configuración + detección de DB
│       ├── models/
│       │   └── schemas.py       # Pydantic models (307 líneas)
│       ├── routes/
│       │   ├── auth.py          # POST /auth/login|register
│       │   ├── users.py         # GET|PUT /users/me
│       │   ├── stores.py        # CRUD /stores
│       │   ├── products.py      # CRUD /products
│       │   ├── orders.py        # Pedidos (415 líneas)
│       │   ├── chat.py          # Chat + pipeline NLP (650 líneas)
│       │   ├── nlp.py           # Motor NLP rule-based (2364 líneas)
│       │   ├── reports.py       # Métricas del agente (201 líneas)
│       │   └── notifications.py # Endpoint de notificaciones
│       ├── services/
│       │   ├── llm.py           # Servicio Ollama/LLaMA (287 líneas)
│       │   └── notification_service.py  # SMTP + chat notify
│       ├── utils/
│       │   └── auth.py          # JWT helpers + FastAPI dependency
│       └── nlp_dataset/
│           └── cochabamba_cercado_orders.json  # 74 ejemplos de entrenamiento
│
├── mobile/                      # React Native (Expo)
│   ├── App.js                   # Navegación principal (Stack + Tabs)
│   └── src/
│       ├── screens/             # 12 pantallas
│       ├── services/
│       │   └── api.js           # Cliente HTTP móvil
│       ├── components/          # Componentes reutilizables
│       └── theme.js             # Colores y estilos globales
│
└── panel/                       # React + Vite
    └── src/
        ├── pages/               # 8 páginas del panel AJE
        ├── components/          # Componentes UI
        └── services/
            └── api.js           # Cliente HTTP del panel
```

---

## Resumen de métricas del código

| Componente | Líneas | Peso |
|---|---|---|
| `nlp.py` — Motor NLP | 2364 | El más complejo del sistema |
| `chat.py` — Pipeline chat | 650 | Lógica de orquestación |
| `ChatScreen.js` — UI chat | 1156 | Pantalla más rica del frontend |
| `schemas.py` — Modelos | 307 | 20+ schemas Pydantic |
| `orders.py` — Pedidos | 415 | Lógica de negocio core |
| `reports.py` — Métricas | 201 | Análisis operacional |
| `llm.py` — LLM service | 287 | Integración Ollama |
| `notification_service.py` | 112 | SMTP + chat notify |

---

*Documento generado automáticamente mediante análisis estático del código fuente del repositorio. Junio 2026.*
