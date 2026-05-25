# 📦 Sprint 2 — Entregables

## Entregable principal

**Chat con procesamiento de lenguaje natural** que permite al cliente escribir pedidos en texto libre y recibir un extracto interpretado automáticamente.

---

## Lista de entregables

### 1. Motor NLP en el backend

- Servicio `nlp_service.py` implementado con:
  - Tokenización y normalización de texto en español.
  - Extracción de cantidades numéricas y escritas.
  - Matching de productos contra catálogo con fuzzy matching.
  - Resolución de fechas relativas.
  - Generación de extracto estructurado.
- Diccionario de sinónimos y variaciones de productos.
- Manejo de unidades de medida.

### 2. Endpoint NLP funcional

- `POST /nlp/parse-order` implementado y probado.
- Entrada: texto libre + store_id.
- Salida: lista de productos, cantidades, precios, subtotales, total, fecha de entrega.
- Validación de stock integrada.
- Manejo de errores con mensajes claros.

### 3. Chat mejorado en la app móvil

- Pantalla de chat rediseñada con burbujas diferenciadas.
- Integración del chat con el endpoint NLP.
- Tarjeta de extracto del pedido en el chat.
- Botones de confirmación ("Confirmar" / "Corregir").
- Indicador de procesamiento.
- Manejo de errores amigable.

### 4. Documentación de pruebas NLP

- Documento con al menos 8 casos de prueba ejecutados.
- Registro de entrada, salida esperada y salida real.
- Análisis de precisión del motor NLP.

---

## Evidencias requeridas

| Evidencia | Descripción |
|---|---|
| Captura de pantalla | Chat con mensaje de pedido escrito por el usuario |
| Captura de pantalla | Extracto del pedido generado automáticamente en el chat |
| Captura de pantalla | Confirmación del pedido desde el chat |
| Captura de pantalla | Manejo de error (producto no encontrado) |
| Captura de pantalla | Manejo de error (stock insuficiente) |
| Log del backend | Request y response del endpoint NLP |
| Documento | Resultados de pruebas del NLP |

---

## Definición de "Done"

- [x] Motor NLP implementado y funcionando.
- [x] Endpoint NLP probado con múltiples casos.
- [x] Chat integrado con NLP en la app móvil.
- [x] Flujo completo de pedido por texto verificado end-to-end.
- [x] Documentación de pruebas completada.
- [x] Código subido al repositorio.
