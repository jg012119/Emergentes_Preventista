# Ciclo de mejora continua NLP - Cochabamba Cercado

Este proyecto mejora el NLP principalmente con:

1. Dataset de frases reales.
2. Aliases del catalogo.
3. Correcciones guardadas por preventistas.
4. Evaluacion automatica antes de cambiar el parser.

## Dataset piloto

Archivo:

```bash
backend/app/nlp_dataset/cochabamba_cercado_orders.json
```

Cada frase debe incluir el resultado esperado:

```json
{
  "id": "cbba-021",
  "text": "Pasame 2 cielitos para manana.",
  "delivery_offset_days": 1,
  "items": [
    {"product": "Agua Cielo 500ml", "presentation": "500ml", "quantity": 2}
  ]
}
```

## Evaluar localmente

Usar SQLite local, sin tocar Supabase:

```bash
backend/.venv/bin/python tools/evaluate_nlp_dataset.py --local
```

Para repetir varias epocas de evaluacion sobre el mismo dataset:

```bash
backend/.venv/bin/python tools/evaluate_nlp_dataset.py --local --epochs 20
```

Salida esperada:

```text
Product accuracy: 100.00%
Presentation accuracy: 100.00%
Quantity accuracy: 100.00%
Date accuracy: 100.00%
Clarification accuracy: 100.00%
```

Para ver detalle de fallos:

```bash
backend/.venv/bin/python tools/evaluate_nlp_dataset.py --local --json
```

## Casos incompletos

Cuando falte contexto, el caso debe declarar que tipo de aclaracion espera:

```json
{
  "id": "cbba-028",
  "text": "Dame Big Cola.",
  "expected_clarification_types": ["quantity", "presentation", "date"],
  "items": [
    {}
  ]
}
```

Tipos usados hoy:

- `quantity`: falta cantidad.
- `product`: falta producto o no se encontro en catalogo.
- `presentation`: falta presentacion/SKU.
- `date`: falta fecha de entrega.
- `customer`: falta tienda/cliente.

## Evaluar contra Supabase

Cuando el catalogo remoto ya tenga los aliases cargados:

```bash
backend/.venv/bin/python tools/evaluate_nlp_dataset.py
```

Si falla en Supabase pero pasa localmente, normalmente falta correr la migracion SQL remota.

## Agregar jerga nueva

Si una frase falla, actualizar aliases en:

```text
backend/database/schema.sql
backend/app/migrations/20260603_add_nlp_catalog_aliases.sql
backend/app/local_db.py
```

Luego correr:

```bash
backend/.venv/bin/python tools/evaluate_nlp_dataset.py --local
```

## Errores de escritura

El parser aplica dos defensas:

- Normalizacion/fuzzy matching controlado para tolerar errores como `bigg`, `sielo`, `chika`, `votl`, `litrso`.
- Aliases `typo_alias` en catalogo para errores frecuentes que ya se vieron en pruebas o uso real.

Si aparece una falta nueva y se repite, agregarla como `typo_alias` y tambien como frase del dataset. Ejemplo:

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

## Feedback del agente

Las respuestas del agente en chat pueden recibir `like` o `dislike`. El backend guarda esos votos en `agent_feedback` asociados al mensaje exacto.

Uso recomendado:

- `like`: la respuesta fue util/correcta.
- `dislike`: la respuesta confundio, no entendio, eligio mal o falto una aclaracion.
- Revisar dislikes cada semana y convertir patrones en reglas, aliases o nuevos casos del dataset.
- No usar el feedback para confirmar pedidos automaticamente; sirve como señal de mejora.

## Flujo de borrador y confirmacion

El flujo productivo queda asi:

1. El usuario escribe un pedido en el chat general.
2. El backend interpreta el texto con NLP.
3. Si falta cliente, producto, cantidad, presentacion o fecha, responde con aclaracion.
4. Si todo esta validado, crea un pedido en estado `borrador`.
5. El chat devuelve el detalle completo: tienda, entrega, productos, precios, total y acciones.
6. El usuario confirma.
7. `POST /orders/{order_id}/confirm` cambia el pedido a `pendiente` y lo deja listo para AJE.

Endpoints:

- `POST /nlp/parse-order`: solo interpreta, no guarda pedido.
- `POST /nlp/draft-order`: interpreta, valida y crea borrador si todo esta completo.
- `POST /orders/{order_id}/confirm`: confirma el borrador y lo envia a AJE como `pendiente`.

## Reglas de trabajo

- No guardar pedidos sin confirmacion humana.
- No aceptar SKU ambiguo si el score es bajo.
- Si el sistema pregunta aclaracion, guardar la correccion.
- Toda correccion repetida debe convertirse en alias o nuevo caso del dataset.
- Las frases del dataset deben reflejar habla real de preventistas/clientes de Cochabamba y alrededores.
