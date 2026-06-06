# Prompt base para el asistente virtual de bebidas AJE Bolivia
# Este módulo es importado por llm.py — el catálogo real se inyecta en runtime.

# Nota: el prompt completo con el catálogo dinámico está en app/services/llm.py
# Este archivo queda como referencia de los ejemplos few-shot y reglas de negocio.

FEW_SHOT_EXAMPLES = """
### Ejemplos few-shot (español boliviano coloquial):

Ejemplo 1 (Pedido simple):
Usuario: "manda 2 coquitas de 3 litros y una agüita cielo"
Respuesta:
{
  "intencion": "pedido",
  "motivo_rechazo": null,
  "productos": [
    {"texto_original": "coquitas de 3 litros", "nombre_detectado": "Coca-Cola", "cantidad": 2, "presentacion": "3L", "sku_sugerido": "Coca-Cola Normal 3L", "requiere_aclaracion": false},
    {"texto_original": "una agüita cielo", "nombre_detectado": "Agua Cielo", "cantidad": 1, "presentacion": null, "sku_sugerido": null, "requiere_aclaracion": true}
  ],
  "fecha_entrega": null,
  "requiere_aclaracion": true,
  "pregunta_aclaracion": "¿De qué tamaño quieres la Agua Cielo? Tenemos de 500ml, 1L y 2.5L",
  "mensaje_libre": null
}

Ejemplo 2 (Pedido con typo y aclaración):
Usuario: "una cocaca light por favor"
Respuesta:
{
  "intencion": "pedido",
  "motivo_rechazo": null,
  "productos": [
    {"texto_original": "cocaca light", "nombre_detectado": "Coca-Cola Light", "cantidad": 1, "presentacion": null, "sku_sugerido": "Coca-Cola Light", "requiere_aclaracion": true}
  ],
  "fecha_entrega": null,
  "requiere_aclaracion": true,
  "pregunta_aclaracion": "¿Qué tamaño de Coca-Cola Light deseas?",
  "mensaje_libre": null
}

Ejemplo 3 (Fuera de alcance - Comida Sólida):
Usuario: "quiero unas papitas"
Respuesta:
{
  "intencion": "fuera_de_alcance",
  "motivo_rechazo": "comida_solida",
  "productos": [],
  "fecha_entrega": null,
  "requiere_aclaracion": false,
  "pregunta_aclaracion": null,
  "mensaje_libre": "❌ Nos especializamos en bebidas. No contamos con comida sólida como papitas."
}

Ejemplo 4 (Fuera de alcance - Alcohol):
Usuario: "manda 6 cervezas y una cheba bien fría"
Respuesta:
{
  "intencion": "fuera_de_alcance",
  "motivo_rechazo": "alcohol",
  "productos": [],
  "fecha_entrega": null,
  "requiere_aclaracion": false,
  "pregunta_aclaracion": null,
  "mensaje_libre": "❌ Lamento informarte que no distribuimos bebidas alcohólicas como la cerveza o cheba."
}

Ejemplo 5 (Consulta catálogo):
Usuario: "qué tienes para el calor?"
Respuesta:
{
  "intencion": "consulta_catalogo",
  "motivo_rechazo": null,
  "productos": [],
  "fecha_entrega": null,
  "requiere_aclaracion": false,
  "pregunta_aclaracion": null,
  "mensaje_libre": "¡Con gusto! Te paso el menú de bebidas disponibles para que elijas."
}

Ejemplo 6 (Solicitud de catálogo):
Usuario: "muéstrame lo que tienen disponible"
Respuesta:
{
  "intencion": "consulta_catalogo",
  "motivo_rechazo": null,
  "productos": [],
  "fecha_entrega": null,
  "requiere_aclaracion": false,
  "pregunta_aclaracion": null,
  "mensaje_libre": "Te paso el menú de bebidas disponibles."
}

Ejemplo 7 (Saludo simple):
Usuario: "hola buenas tardes"
Respuesta:
{
  "intencion": "saludo",
  "motivo_rechazo": null,
  "productos": [],
  "fecha_entrega": null,
  "requiere_aclaracion": false,
  "pregunta_aclaracion": null,
  "mensaje_libre": "¡Hola! 😊 Soy tu asistente de pedidos AJE. ¿Qué bebidas te envío hoy?"
}

Ejemplo 8 (Saludo con identificación):
Usuario: "buenas! soy el preventista de zona norte"
Respuesta:
{
  "intencion": "saludo",
  "motivo_rechazo": null,
  "productos": [],
  "fecha_entrega": null,
  "requiere_aclaracion": false,
  "pregunta_aclaracion": null,
  "mensaje_libre": "¡Buenas! 👋 ¿Qué pedido armamos hoy?"
}

Ejemplo 9 (Confirmación):
Usuario: "sí, confirmo el pedido"
Respuesta:
{
  "intencion": "confirmacion",
  "motivo_rechazo": null,
  "productos": [],
  "fecha_entrega": null,
  "requiere_aclaracion": false,
  "pregunta_aclaracion": null,
  "mensaje_libre": null
}
"""

REJECTION_MESSAGES = {
    "solid_food": (
        "❌ Lamento informarte que no contamos con ese producto, "
        "ya que nos especializamos exclusivamente en el abastecimiento "
        "de productos líquidos y bebidas."
    ),
    "alcohol": (
        "❌ Lamento informarte que no distribuimos bebidas alcohólicas."
    ),
    "sin_stock": (
        "⚠️ Ese producto no está disponible en este momento. "
        "¿Te gustaría ver el catálogo completo?"
    ),
}
