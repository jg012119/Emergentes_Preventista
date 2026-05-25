# 💬 Sprint 2 — Chat con Lenguaje Natural (Texto)

## Objetivo

Implementar el **procesamiento de lenguaje natural (NLP) para texto escrito** en el chat de la app móvil, permitiendo que el cliente escriba su pedido en lenguaje libre y el sistema interprete automáticamente los productos, cantidades, precios y fecha de entrega.

---

## Alcance del sprint

### ✅ Incluido

- **Endpoint NLP** (`POST /nlp/parse-order`) para interpretar texto libre.
- **Motor de extracción** de productos, cantidades y fechas desde texto en español.
- **Matching de productos** contra el catálogo de AJE (fuzzy matching).
- **Resolución de fechas** relativas ("para el viernes", "mañana", "la próxima semana").
- **Generación automática de extracto** del pedido desde el texto interpretado.
- **Integración del chat** como entrada principal de pedidos en la app.
- **Flujo de confirmación** después de la interpretación.
- **Manejo de errores** cuando no se puede interpretar el mensaje.

### ❌ Excluido (se hará en Sprint 3)

- Reconocimiento de voz.
- Entrada por micrófono.

---

## Responsables

| Componente | Responsable | Apoyo |
|---|---|---|
| Motor NLP en backend | Luz Laredo | Jairo |
| Integración chat → NLP | Luz Laredo | Valentina |
| UI del chat mejorada | Valentina Trigo | Luz |
| Testing del NLP | Todo el equipo | — |

---

## Duración estimada

**1 semana**

---

## Dependencias

- Sprint 1 completado (backend, BD, app móvil funcional).
- Catálogo de productos insertado en la base de datos.
- Endpoints de pedidos y chat funcionando.

---

## Notas técnicas

- El NLP **no usa IA entrenada desde cero**; utiliza reglas de extracción y fuzzy matching contra el catálogo.
- Se pueden usar librerías como `spaCy`, `dateparser`, `fuzzywuzzy` o `rapidfuzz`.
- El sistema debe manejar variaciones comunes del español boliviano.
- Si el sistema no puede interpretar un producto, debe responder pidiendo aclaración.
- El extracto debe mostrar todos los datos interpretados para que el usuario confirme.
