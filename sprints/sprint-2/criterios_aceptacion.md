# ✅ Sprint 2 — Criterios de Aceptación

## Procesamiento de lenguaje natural

- [ ] El endpoint `POST /nlp/parse-order` recibe texto libre y retorna productos, cantidades, precios y total.
- [ ] El sistema identifica correctamente productos del catálogo con fuzzy matching.
- [ ] El sistema extrae cantidades numéricas y escritas ("4", "cuatro", "una docena").
- [ ] El sistema resuelve fechas relativas ("mañana", "el viernes", "la próxima semana").
- [ ] El sistema asigna precio unitario desde el catálogo de productos.
- [ ] El sistema calcula subtotales y total correctamente.
- [ ] El sistema valida stock disponible antes de generar el extracto.

---

## Manejo de errores del NLP

- [ ] Si no se detecta ningún producto válido, el sistema responde con un mensaje claro.
- [ ] Si un producto no existe en el catálogo, el sistema sugiere productos similares.
- [ ] Si no se especifica cantidad, el sistema asume 1 o pregunta al usuario.
- [ ] Si el stock es insuficiente, el sistema informa la cantidad disponible.
- [ ] Si el mensaje no contiene un pedido (ej: "Hola"), el sistema responde apropiadamente.

---

## Chat integrado con NLP

- [ ] El cliente puede escribir un pedido en lenguaje natural en el chat.
- [ ] El chat envía el texto al endpoint NLP y muestra la respuesta.
- [ ] El extracto del pedido se muestra como tarjeta formateada en el chat.
- [ ] El cliente puede confirmar el pedido desde el chat con un botón.
- [ ] El cliente puede pedir correcciones escribiendo un nuevo mensaje.
- [ ] Los mensajes se diferencian visualmente (burbuja de usuario vs burbuja del sistema).
- [ ] Se muestra un indicador de "procesando" mientras el NLP trabaja.

---

## Flujo completo

- [ ] El cliente escribe: "Quiero 4 Coca-Colas y 2 paquetes de Bolt para el viernes".
- [ ] El sistema responde con un extracto mostrando los productos, cantidades, precios y total.
- [ ] El cliente confirma.
- [ ] El pedido se guarda en estado Pendiente con los datos correctos.
- [ ] El pedido aparece en el panel de AJE.

---

## Criterio global de completitud

> **El Sprint 2 se considera completo cuando el cliente puede escribir un pedido en lenguaje natural en el chat, el sistema interpreta correctamente los productos, cantidades y precios, genera un extracto y el cliente puede confirmarlo para crear un pedido real en el sistema.**
