# 📝 Sprint 2 — Backlog de Tareas

## Épica 1: Motor de procesamiento de lenguaje natural

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S2-001 | Crear servicio `nlp_service.py` en `backend/app/services/` | Alta | 1h |
| S2-002 | Implementar tokenización y normalización de texto en español | Alta | 3h |
| S2-003 | Implementar extracción de cantidades numéricas y escritas ("4", "cuatro", "una docena") | Alta | 4h |
| S2-004 | Implementar matching de nombres de productos contra catálogo (fuzzy matching con `rapidfuzz`) | Alta | 4h |
| S2-005 | Implementar resolución de fechas relativas ("mañana", "el viernes", "la próxima semana") usando `dateparser` | Alta | 3h |
| S2-006 | Implementar extracción de observaciones del pedido | Media | 2h |
| S2-007 | Crear diccionario de sinónimos y variaciones de nombres de productos | Alta | 3h |
| S2-008 | Manejar unidades de medida ("paquetes", "cajas", "unidades", "six-pack") | Alta | 3h |
| S2-009 | Implementar manejo de múltiples productos en un solo mensaje | Alta | 3h |
| S2-010 | Implementar respuesta de error cuando no se detectan productos válidos | Alta | 2h |

---

## Épica 2: Endpoint NLP

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S2-011 | Crear endpoint `POST /nlp/parse-order` | Alta | 2h |
| S2-012 | Validar que los productos encontrados existan en el catálogo | Alta | 2h |
| S2-013 | Asignar precio unitario desde el catálogo a cada producto encontrado | Alta | 1h |
| S2-014 | Calcular subtotales y total del pedido | Alta | 1h |
| S2-015 | Validar stock disponible para cada producto | Alta | 2h |
| S2-016 | Generar respuesta estructurada con extracto del pedido | Alta | 2h |
| S2-017 | Retornar flag `requires_confirmation: true` para flujo de confirmación | Alta | 30min |
| S2-018 | Manejar caso de producto no encontrado: sugerir productos similares | Media | 3h |
| S2-019 | Manejar caso de stock insuficiente: informar al usuario | Alta | 2h |

---

## Épica 3: Integración del chat con NLP

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S2-020 | Como cliente, quiero escribir un pedido en el chat y que el sistema lo interprete automáticamente | Alta | 4h |
| S2-021 | Como cliente, quiero ver el extracto generado automáticamente desde mi texto | Alta | 3h |
| S2-022 | Como cliente, quiero confirmar el pedido interpretado o pedir correcciones | Alta | 3h |
| S2-023 | Como cliente, quiero que el sistema me pregunte si faltó algún dato (tienda, fecha) | Media | 2h |
| S2-024 | Conectar la entrada de texto del chat con el endpoint `/nlp/parse-order` | Alta | 2h |
| S2-025 | Mostrar mensajes del sistema con formato diferenciado (bot vs usuario) | Alta | 2h |
| S2-026 | Implementar botones de confirmación en el chat ("Confirmar" / "Corregir") | Alta | 2h |

---

## Épica 4: Mejoras de UI del chat

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S2-027 | Rediseñar pantalla de chat con burbujas de mensajes (usuario vs sistema) | Alta | 3h |
| S2-028 | Mostrar extracto del pedido como tarjeta formateada en el chat | Alta | 3h |
| S2-029 | Agregar indicador de "escribiendo..." mientras el NLP procesa | Media | 1h |
| S2-030 | Agregar scroll automático al último mensaje | Media | 1h |
| S2-031 | Mostrar errores del NLP de forma amigable ("No entendí qué producto querés pedir") | Alta | 2h |

---

## Épica 5: Casos de prueba del NLP

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S2-032 | Probar: "Quiero 4 Coca-Colas y 2 paquetes de Bolt para el viernes" | Alta | 1h |
| S2-033 | Probar: "Mándame 10 Big Cola de 3 litros" | Alta | 1h |
| S2-034 | Probar: "Necesito una caja de Sporade y dos Six-Pack de Cifrut" | Alta | 1h |
| S2-035 | Probar: "Quiero Coca-Cola" (sin cantidad → el sistema debe preguntar) | Alta | 1h |
| S2-036 | Probar: "Hola, buenos días" (sin pedido → el sistema debe responder adecuadamente) | Media | 1h |
| S2-037 | Probar: "Quiero 5 productos XYZ" (producto inexistente → sugerencia) | Alta | 1h |
| S2-038 | Probar: "Dame 100 Coca-Colas" (stock insuficiente → aviso) | Alta | 1h |
| S2-039 | Probar variaciones del español: "Mandame", "Quiero pedirles", "Me puede dar" | Media | 2h |
| S2-040 | Documentar resultados de todas las pruebas NLP | Alta | 2h |

---

## Resumen de estimaciones

| Épica | Tareas | Horas estimadas |
|---|---|---|
| Motor NLP | 10 | 28h |
| Endpoint NLP | 9 | 15.5h |
| Integración chat + NLP | 7 | 18h |
| Mejoras UI del chat | 5 | 10h |
| Pruebas NLP | 9 | 11h |
| **TOTAL** | **40** | **~82.5h** |
