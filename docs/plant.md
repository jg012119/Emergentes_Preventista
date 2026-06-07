Plan detallado para que funcione correctamente con Llama
1. Mantener la arquitectura de 3 capas, pero ajustar responsabilidades

Tu arquitectura actual está bien:

Mensaje usuario
   ↓
Capa 1: Reglas + fuzzy matching
   ↓ si no entiende
Capa 2: Llama / Ollama
   ↓ si falla
Capa 3: Respuesta hardcoded

Pero la Capa 2 debe cambiar.

Actualmente el LLM interpreta y muestra productos, pero no crea borradores. Eso está causando el problema de que el usuario diga “sí” y el sistema ya no tenga un pedido real pendiente.

La arquitectura correcta debería ser:

Mensaje usuario
   ↓
Reglas rápidas
   ↓
NLP de reglas
   ↓ si falla
Llama extractor semántico
   ↓
Validador backend
   ↓
Resolver producto real por ID / SKU / presentación
   ↓
Crear borrador
   ↓
Mostrar resumen
   ↓
Confirmación obligatoria del preventista

Llama 3.1 8B Instruct es razonable para este caso porque es un modelo instructivo multilingüe, soporta español y está pensado para diálogo asistente; además su ficha indica contexto de hasta 128k tokens, aunque en Ollama el contexto práctico depende de la VRAM configurada.

2. Usar JSON Schema obligatorio con Ollama

No conviene pedirle al modelo:

Respóndeme en JSON

Eso puede fallar.

Ollama ya permite structured outputs usando format con JSON Schema. La documentación oficial indica que se puede pasar un schema al campo format, e incluso recomienda validar la salida con Pydantic.

Tu ask_llm() debería funcionar así:

response = await client.chat(
    model=OLLAMA_MODEL,
    messages=messages,
    stream=False,
    format=LlamaIntent.model_json_schema(),
    options={
        "temperature": 0,
        "top_p": 0.2,
        "num_ctx": 4096,
    },
    keep_alive="30m",
)

Y luego:

parsed = LlamaIntent.model_validate_json(response["message"]["content"])

Esto reduce muchísimo los errores de formato.

3. Nuevo schema recomendado para Llama

El LLM no debería devolver solamente texto libre. Debe devolver una estructura así:

{
  "intencion": "pedido",
  "confianza": 0.86,
  "motivo_rechazo": null,
  "mensaje_libre": null,
  "productos": [
    {
      "texto_original": "cuatro cielos chicos",
      "nombre_detectado": "agua cielo",
      "cantidad": 4,
      "presentacion": "500ml",
      "product_id_sugerido": null,
      "sku_sugerido": null,
      "requiere_aclaracion": false
    }
  ],
  "fecha_entrega": "2026-06-07",
  "requiere_aclaracion": false,
  "pregunta_aclaracion": null
}

Intenciones permitidas:

pedido
consulta_catalogo
estado_pedido
listar_pedidos
saludo
fuera_de_alcance
confirmacion
negacion
aclaracion
ambiguo

Motivos de rechazo:

alcohol
comida_solida
competencia
producto_inexistente
fuera_de_dominio
mensaje_inseguro

El punto importante: Llama puede sugerir, pero no decidir definitivamente.

4. Eliminar validación por substring

Tu problema actual:

if sku_sugerido.lower() in pname or pname in sku_sugerido.lower():

Eso puede hacer que:

Big Cola

termine seleccionando cualquier presentación:

Big Cola 500ml
Big Cola 2L
Big Cola 3L

La nueva prioridad de validación debería ser:

1. product_id exacto
2. sku exacto
3. alias exacto
4. marca + sabor + presentación
5. fuzzy matching con RapidFuzz
6. si hay empate o baja confianza → pedir aclaración

RapidFuzz es buena opción, pero ojo: desde RapidFuzz 3.0 no preprocesa strings automáticamente; por eso tu normalización manual de acentos, minúsculas y espacios sigue siendo necesaria.

5. Crear una capa nueva: product_resolver.py

Te recomiendo separar la lógica de resolución de productos en un servicio propio:

backend/app/services/product_resolver.py

Responsabilidad:

resolve_llm_product(
    detected_name: str,
    quantity: int,
    presentation: str | None,
    catalog: list[Product]
) -> ResolvedProduct

Resultado esperado:

{
  "status": "matched",
  "product_id": "uuid",
  "sku": "AJE-CIELO-500",
  "name": "Agua Cielo 500ml",
  "quantity": 4,
  "confidence": 0.94,
  "match_reason": "alias+presentation"
}

Estados posibles:

matched
ambiguous
not_found
missing_presentation
missing_quantity
blocked

Ejemplo:

Usuario: "dame 4 cielitos"
Llama: agua cielo, cantidad 4, presentación null
Resolver: hay Cielo 500ml, 1L, 2L
Respuesta: "¿Te refieres a Agua Cielo 500ml, 1L o 2L?"
6. Inyectar catálogo real, pero compacto

No metas todo el catálogo con descripciones largas. Eso aumenta tokens y latencia.

Usa una versión compacta:

[
  {
    "id": "p_001",
    "sku": "CIELO-500",
    "name": "Agua Cielo 500ml",
    "brand": "Cielo",
    "category": "agua",
    "presentation": "500ml",
    "aliases": ["cielo chico", "cielito", "agua chica"]
  },
  {
    "id": "p_002",
    "sku": "BIG-2L",
    "name": "Big Cola 2L",
    "brand": "Big Cola",
    "category": "gaseosa",
    "presentation": "2L",
    "aliases": ["big familiar", "big dos litros"]
  }
]

Mejor todavía: antes de llamar a Llama, hacer un pre-filtrado local:

Mensaje: "quiero 3 cielitos y 2 volt"

Enviar al LLM solo candidatos relacionados con:

cielo
volt
agua
energizante

No todo el catálogo.

7. Crear tabla de aliases editable

No pongas toda la jerga en código. Debe estar en base de datos.

Tabla recomendada:

product_aliases

Campos:

id
product_id
alias
normalized_alias
region
source
confidence
active
created_at
updated_at

Ejemplo:

cielito → Agua Cielo 500ml
orito → Oro
coquita → Coca Cola / Big Cola, según catálogo real
voltcito → Volt

Campo source:

manual
feedback
llm_suggested
imported_dataset

Así, cuando un preventista use una palabra nueva y el agente falle, esa frase se puede convertir en alias sin tocar código.

8. Corregir el problema principal: Llama debe crear borrador indirectamente

Flujo recomendado cuando Llama detecta pedido:

llm_result = await ask_llm(...)
validated = LlamaIntent.model_validate_json(llm_result)

if validated.intencion == "pedido":
    resolved_items = resolve_products(validated.productos)

    if all_items_are_matched(resolved_items):
        draft = create_order_draft(
            user_id=user_id,
            items=resolved_items,
            delivery_date=validated.fecha_entrega
        )
        return build_draft_confirmation_message(draft)

    if has_ambiguity(resolved_items):
        save_pending_clarification(...)
        return build_clarification_question(...)

O sea:

Llama interpreta
Backend valida
Backend crea borrador
Usuario confirma
Backend pasa a pendiente

Nunca:

Llama confirma pedido directamente

Eso mantiene tu regla de negocio de confirmación obligatoria.

9. Guardar contexto operativo, no solo últimos 6 mensajes

El historial de 6 mensajes ayuda, pero no basta.

Crea una tabla o campo de estado:

chat_session_state

Campos:

user_id
active_order_id
last_detected_products
pending_clarification_type
pending_clarification_payload
last_store_id
last_delivery_date
updated_at
expires_at

Ejemplo:

Usuario: quiero 3 cielos
Sistema: ¿500ml, 1L o 2L?
Usuario: de litro
Sistema: crea borrador con Agua Cielo 1L x3

Esto no debe depender solamente del LLM. Debe estar persistido.

10. Mejorar el prompt del sistema

El prompt debe ser estricto:

Eres un extractor de intención para pedidos AJE Bolivia.
No eres un chatbot libre.
Devuelve únicamente JSON válido según el schema.

Reglas:
- No inventes productos.
- No confirmes pedidos.
- Si falta cantidad, usa 1 solo si el usuario dice "una", "un", "uno".
- Si falta presentación y hay varias posibles, marca requiere_aclaracion=true.
- Si menciona alcohol, motivo_rechazo="alcohol".
- Si menciona comida sólida, motivo_rechazo="comida_solida".
- Si menciona competencia, motivo_rechazo="competencia".
- Usa el catálogo proporcionado.
- Prioriza aliases regionales de Cochabamba Cercado.

También meter ejemplos few-shot, pero cortos:

"quiero 3 cielitos chicos"
→ Agua Cielo, cantidad 3, presentación 500ml

"pasame dos volt y una big familiar"
→ Volt x2, Big Cola 2L x1

"quiero chela"
→ fuera_de_alcance, alcohol
11. Configuración recomendada de Ollama

Para producción inicial:

LLM_FALLBACK_ENABLED=true
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=aje-preventista
OLLAMA_TIMEOUT=20
OLLAMA_KEEP_ALIVE=30m
OLLAMA_NUM_PARALLEL=1
OLLAMA_MAX_QUEUE=20
OLLAMA_CONTEXT_LENGTH=4096

Ollama permite keep_alive para mantener el modelo cargado y reducir tiempos después de la primera llamada; también se puede configurar cuánto tiempo se mantiene en memoria.

Para concurrencia, cuidado: Ollama documenta que OLLAMA_NUM_PARALLEL aumenta el uso de memoria porque escala con OLLAMA_NUM_PARALLEL * OLLAMA_CONTEXT_LENGTH. Por eso, si no tienes GPU fuerte, mejor empezar con 1 y cola pequeña.

12. Métricas obligatorias

Guarda cada ejecución del LLM en una tabla:

llm_logs

Campos:

id
user_id
message
intent
raw_response
parsed_json
success
error
latency_ms
prompt_tokens
eval_tokens
model
created_at

Ollama devuelve métricas como total_duration, load_duration, prompt_eval_count, eval_count y eval_duration, útiles para medir latencia real.

Con eso puedes saber:

cuánto tarda la capa 1
cuánto tarda Llama
cuántas veces falla JSON
cuántas veces hay ambigüedad
cuántas veces se crea borrador
cuántos dislikes recibe
Roadmap de implementación
Fase 1 — Estabilizar Llama

Objetivo: que Llama siempre devuelva JSON válido.

Tareas:

1. Crear Pydantic model: LlamaIntent
2. Usar format=LlamaIntent.model_json_schema()
3. temperature=0
4. Validar con model_validate_json()
5. Guardar logs del raw response
6. Si falla, hacer retry una sola vez
7. Si vuelve a fallar, ir a hardcoded fallback

Resultado esperado:

El LLM deja de responder texto libre raro.
Fase 2 — Resolver productos correctamente

Objetivo: eliminar el bug del substring.

Tareas:

1. Crear product_resolver.py
2. Resolver por product_id exacto
3. Resolver por SKU exacto
4. Resolver por alias exacto
5. Resolver por marca + presentación
6. Usar fuzzy solo como último recurso
7. Si hay empate, pedir aclaración

Resultado esperado:

"Big Cola" ya no elige cualquier Big Cola.
Fase 3 — Crear borradores desde salida validada de Llama

Objetivo: que si Llama entiende un pedido, el sistema cree borrador real.

Tareas:

1. En _llm_fallback_reply(), si intencion == pedido
2. Validar productos
3. Si todo está claro, llamar a create_order_draft()
4. Guardar active_order_id
5. Responder con resumen + @@action order
6. Esperar confirmación explícita

Resultado esperado:

Usuario: "quiero 2 volt y 3 cielos chicos"
Sistema: crea borrador real
Usuario: "sí"
Sistema: confirma el borrador
Fase 4 — Memoria conversacional operativa

Objetivo: que las aclaraciones no se pierdan.

Tareas:

1. Crear chat_session_state
2. Guardar aclaraciones pendientes
3. Guardar último borrador activo
4. Guardar última fecha de entrega
5. Guardar últimos productos sugeridos
6. Expirar estados viejos después de 5 a 10 minutos

Resultado esperado:

Sistema entiende respuestas cortas como "de litro", "sí", "mañana", "dos".
Fase 5 — Dataset y mejora continua

Objetivo: que cada error mejore el agente.

Tareas:

1. Revisar agent_feedback semanalmente
2. Sacar mensajes con dislike
3. Clasificarlos en:
   - alias faltante
   - producto ambiguo
   - mala presentación
   - mala intención
   - rechazo incorrecto
4. Agregar alias a DB
5. Agregar ejemplos al dataset
6. Ejecutar test_llm_fallback.py

Métricas mínimas:

Exactitud de intención: mínimo 95%
Exactitud de producto: mínimo 90%
JSON válido: mínimo 99%
Pedidos ambiguos bien aclarados: mínimo 90%
Latencia LLM con GPU: ideal < 3s
Latencia LLM en CPU: evitar producción
Flujo final recomendado
1. Usuario escribe:
   "mandame 4 cielitos y 2 volt para mañana"

2. Capa 1 intenta resolver.
   Si puede, crea borrador.

3. Si Capa 1 no puede:
   Llama devuelve JSON:
   Agua Cielo 500ml x4
   Volt x2
   fecha mañana

4. Backend valida contra catálogo real.

5. Backend crea borrador.

6. Sistema responde:
   "Listo, preparé este borrador..."

7. Usuario confirma:
   "sí"

8. Backend cambia:
   borrador → pendiente
Prioridad real de cambios

Hazlo en este orden:

1. JSON Schema obligatorio con Pydantic
2. product_resolver.py
3. Eliminar substring matching
4. Crear borrador desde Llama validado
5. chat_session_state
6. Tabla product_aliases
7. llm_logs
8. Suite de pruebas con 100+ frases reales de Cochabamba
9. Optimización Ollama/GPU