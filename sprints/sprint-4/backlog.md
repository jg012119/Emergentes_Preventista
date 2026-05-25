# 📝 Sprint 4 — Backlog de Tareas

## Épica 1: Pruebas unitarias del backend

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S4-001 | Escribir tests para `POST /auth/register` (caso exitoso, email duplicado, datos faltantes) | Alta | 2h |
| S4-002 | Escribir tests para `POST /auth/login` (credenciales correctas, incorrectas, usuario inexistente) | Alta | 2h |
| S4-003 | Escribir tests para CRUD de tiendas (crear, listar, editar, eliminar) | Alta | 2h |
| S4-004 | Escribir tests para CRUD de productos (crear, listar, editar, desactivar) | Alta | 2h |
| S4-005 | Escribir tests para creación de pedido borrador (con stock, sin stock, productos inválidos) | Alta | 3h |
| S4-006 | Escribir tests para confirmación de pedido (pedido válido, pedido inexistente, doble confirmación) | Alta | 2h |
| S4-007 | Escribir tests para cambio de estado del pedido (transiciones válidas e inválidas) | Alta | 2h |
| S4-008 | Escribir tests para el endpoint NLP (`POST /nlp/parse-order`) con múltiples entradas | Alta | 3h |
| S4-009 | Escribir tests para notificaciones por chat y correo | Media | 2h |
| S4-010 | Escribir tests para validación de JWT (token válido, expirado, ausente) | Alta | 2h |

---

## Épica 2: Pruebas de integración

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S4-011 | Probar flujo completo: registro → login → crear tienda → crear pedido manual → confirmar | Alta | 3h |
| S4-012 | Probar flujo completo: escribir pedido en chat → NLP → extracto → confirmar → pedido creado | Alta | 3h |
| S4-013 | Probar flujo completo: dictar pedido por voz → texto → NLP → extracto → confirmar | Alta | 3h |
| S4-014 | Probar flujo completo: pedido pendiente → AJE cambia estado → notificación chat + correo | Alta | 3h |
| S4-015 | Probar integración app móvil ↔ backend FastAPI (todas las pantallas) | Alta | 4h |
| S4-016 | Probar integración panel web ↔ backend FastAPI (todos los módulos) | Alta | 4h |
| S4-017 | Probar integración base de datos: verificar integridad referencial y datos consistentes | Alta | 2h |

---

## Épica 3: Pruebas del NLP con escenarios variados

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S4-018 | Probar 10 frases diferentes de pedidos con variaciones del español | Alta | 3h |
| S4-019 | Probar pedidos con cantidades escritas en texto ("cuatro", "una docena", "medio") | Alta | 2h |
| S4-020 | Probar pedidos con nombres parciales de productos ("coca", "big", "bolt") | Alta | 2h |
| S4-021 | Probar pedidos con múltiples productos en una sola frase | Alta | 2h |
| S4-022 | Probar pedidos con fechas relativas variadas ("mañana", "pasado mañana", "el lunes") | Alta | 2h |
| S4-023 | Probar pedidos con errores ortográficos comunes | Media | 2h |
| S4-024 | Probar mensajes que NO son pedidos ("Hola", "Gracias", "¿Cuánto cuesta?") | Media | 1h |
| S4-025 | Documentar tasa de precisión del NLP (productos correctos / total intentados) | Alta | 2h |

---

## Épica 4: Pruebas de reconocimiento de voz

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S4-026 | Probar dictado con 5 frases diferentes en ambiente silencioso | Alta | 2h |
| S4-027 | Probar dictado con 5 frases diferentes en ambiente con ruido moderado | Alta | 2h |
| S4-028 | Probar dictado con diferentes velocidades de habla (lento, normal, rápido) | Alta | 2h |
| S4-029 | Probar dictado con diferentes acentos del equipo | Media | 2h |
| S4-030 | Probar corrección manual después de dictado incorrecto | Alta | 1h |
| S4-031 | Probar grabación con permisos denegados | Alta | 1h |
| S4-032 | Probar dictado sin conexión a internet | Media | 1h |
| S4-033 | Documentar tasa de precisión del reconocimiento de voz | Alta | 2h |

---

## Épica 5: Pruebas de usabilidad

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S4-034 | Evaluar facilidad de registro e inicio de sesión (app móvil) | Alta | 1h |
| S4-035 | Evaluar facilidad de registro de tienda con ubicación | Alta | 1h |
| S4-036 | Evaluar facilidad de crear pedido manual (selección de productos) | Alta | 1h |
| S4-037 | Evaluar facilidad de crear pedido por chat escrito | Alta | 1h |
| S4-038 | Evaluar facilidad de crear pedido por voz | Alta | 1h |
| S4-039 | Evaluar claridad del extracto del pedido | Alta | 1h |
| S4-040 | Evaluar facilidad de confirmar un pedido | Alta | 30min |
| S4-041 | Evaluar navegación general de la app móvil | Media | 1h |
| S4-042 | Evaluar facilidad de uso del panel web de AJE | Alta | 1h |
| S4-043 | Evaluar claridad de las notificaciones | Media | 1h |
| S4-044 | Solicitar retroalimentación a 3 usuarios de prueba (simulados) | Alta | 3h |
| S4-045 | Documentar hallazgos de usabilidad con recomendaciones | Alta | 2h |

---

## Épica 6: Pruebas de aceptación

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S4-046 | Verificar: El usuario puede registrarse | Alta | 30min |
| S4-047 | Verificar: El usuario puede registrar su tienda con nombre, dirección y ubicación | Alta | 30min |
| S4-048 | Verificar: El usuario puede escribir un pedido y el sistema lo interpreta | Alta | 30min |
| S4-049 | Verificar: El usuario puede dictar un pedido por voz | Alta | 30min |
| S4-050 | Verificar: El sistema convierte la voz en texto | Alta | 30min |
| S4-051 | Verificar: El sistema identifica productos y cantidades | Alta | 30min |
| S4-052 | Verificar: El sistema muestra precio unitario, subtotal y total | Alta | 30min |
| S4-053 | Verificar: El sistema muestra un extracto antes de enviar | Alta | 30min |
| S4-054 | Verificar: El usuario puede confirmar el pedido | Alta | 30min |
| S4-055 | Verificar: El pedido se guarda en estado Pendiente | Alta | 30min |
| S4-056 | Verificar: El pedido aparece en el panel de AJE | Alta | 30min |
| S4-057 | Verificar: AJE puede cambiar el estado del pedido | Alta | 30min |
| S4-058 | Verificar: El cliente recibe notificación por chat | Alta | 30min |
| S4-059 | Verificar: El cliente recibe notificación por correo | Alta | 30min |
| S4-060 | Verificar: El sistema valida stock básico | Alta | 30min |
| S4-061 | Verificar: El MVP puede ser presentado en una prueba real simulada | Alta | 1h |

---

## Épica 7: Corrección de errores y regresión

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S4-062 | Clasificar errores encontrados por severidad (Crítico, Alto, Medio, Bajo) | Alta | 2h |
| S4-063 | Corregir todos los errores clasificados como "Crítico" | Alta | 8h |
| S4-064 | Corregir todos los errores clasificados como "Alto" | Alta | 6h |
| S4-065 | Corregir errores clasificados como "Medio" (según tiempo disponible) | Media | 4h |
| S4-066 | Ejecutar pruebas de regresión después de cada corrección | Alta | 4h |
| S4-067 | Verificar que las correcciones no introdujeron nuevos errores | Alta | 2h |

---

## Épica 8: Documentación de pruebas

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S4-068 | Crear documento resumen de pruebas unitarias (resultados, cobertura) | Alta | 2h |
| S4-069 | Crear documento resumen de pruebas de integración (flujos probados, resultados) | Alta | 2h |
| S4-070 | Crear documento resumen de pruebas de NLP (precisión, casos fallidos) | Alta | 2h |
| S4-071 | Crear documento resumen de pruebas de voz (precisión, condiciones) | Alta | 2h |
| S4-072 | Crear documento resumen de pruebas de usabilidad (hallazgos, recomendaciones) | Alta | 2h |
| S4-073 | Crear documento resumen de pruebas de aceptación (checklist de criterios) | Alta | 2h |
| S4-074 | Crear registro de errores encontrados y corregidos (bug tracker) | Alta | 2h |

---

## Resumen de estimaciones

| Épica | Tareas | Horas estimadas |
|---|---|---|
| Pruebas unitarias backend | 10 | 22h |
| Pruebas de integración | 7 | 22h |
| Pruebas NLP | 8 | 16h |
| Pruebas de voz | 8 | 13h |
| Pruebas de usabilidad | 12 | 14.5h |
| Pruebas de aceptación | 16 | 9h |
| Corrección de errores | 6 | 26h |
| Documentación | 7 | 14h |
| **TOTAL** | **74** | **~136.5h** |
