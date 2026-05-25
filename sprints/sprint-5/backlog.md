# 📝 Sprint 5 — Backlog de Tareas

## Épica 1: Diseño y ejecución de encuestas de satisfacción

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S5-001 | Diseñar encuesta de satisfacción para clientes (tiendas/mayoristas) | Alta | 3h |
| S5-002 | Diseñar encuesta de satisfacción para la empresa (AJE simulada) | Alta | 2h |
| S5-003 | Definir escala de evaluación (Likert 1-5) para cada pregunta | Alta | 1h |
| S5-004 | Crear formulario digital de la encuesta (Google Forms o similar) | Alta | 2h |
| S5-005 | Reclutar al menos 5 usuarios de prueba para rol de cliente | Alta | 2h |
| S5-006 | Reclutar al menos 2 usuarios de prueba para rol de empresa AJE | Alta | 1h |
| S5-007 | Ejecutar sesiones de prueba guiadas con cada usuario | Alta | 6h |
| S5-008 | Recopilar todas las respuestas de las encuestas | Alta | 2h |

### Preguntas sugeridas — Encuesta de clientes

| # | Pregunta | Tipo |
|---|---|---|
| 1 | ¿Qué tan fácil fue registrarse en la aplicación? | Likert 1-5 |
| 2 | ¿Qué tan fácil fue registrar su tienda y ubicación? | Likert 1-5 |
| 3 | ¿Qué tan fácil fue crear un pedido seleccionando productos? | Likert 1-5 |
| 4 | ¿Qué tan fácil fue crear un pedido escribiendo en el chat? | Likert 1-5 |
| 5 | ¿Qué tan fácil fue crear un pedido usando la voz? | Likert 1-5 |
| 6 | ¿El sistema interpretó correctamente su pedido? | Likert 1-5 |
| 7 | ¿El extracto del pedido fue claro y correcto? | Likert 1-5 |
| 8 | ¿Qué tan útiles fueron las notificaciones de estado? | Likert 1-5 |
| 9 | ¿Usaría esta aplicación para hacer pedidos reales? | Likert 1-5 |
| 10 | ¿Qué tan satisfecho está con la aplicación en general? | Likert 1-5 |
| 11 | ¿Qué mejoraría de la aplicación? | Texto libre |
| 12 | ¿Qué fue lo que más le gustó? | Texto libre |
| 13 | ¿Prefiere hacer pedidos por texto, por voz o seleccionando productos? | Opción múltiple |
| 14 | ¿El sistema es más rápido que pedir por WhatsApp o llamada? | Sí/No |
| 15 | ¿Recomendaría esta aplicación a otros comerciantes? | Sí/No |

### Preguntas sugeridas — Encuesta empresa AJE

| # | Pregunta | Tipo |
|---|---|---|
| 1 | ¿Qué tan fácil fue usar el panel de gestión de pedidos? | Likert 1-5 |
| 2 | ¿La información del pedido es suficiente para procesarlo? | Likert 1-5 |
| 3 | ¿Qué tan útil es ver los productos, cantidades y precios del pedido? | Likert 1-5 |
| 4 | ¿Qué tan fácil fue cambiar el estado del pedido? | Likert 1-5 |
| 5 | ¿La gestión de productos y stock fue intuitiva? | Likert 1-5 |
| 6 | ¿El sistema reduce el trabajo manual de recibir pedidos? | Likert 1-5 |
| 7 | ¿Usaría este sistema en lugar del proceso actual de pedidos? | Likert 1-5 |
| 8 | ¿Qué funcionalidad adicional necesitaría? | Texto libre |
| 9 | ¿Qué tan satisfecho está con el panel en general? | Likert 1-5 |
| 10 | ¿Recomendaría este sistema a la empresa? | Sí/No |

---

## Épica 2: Métricas de uso del sistema

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S5-009 | Registrar cantidad de pedidos creados durante las pruebas | Alta | 1h |
| S5-010 | Registrar tiempo promedio para crear un pedido manual | Alta | 2h |
| S5-011 | Registrar tiempo promedio para crear un pedido por chat (texto NLP) | Alta | 2h |
| S5-012 | Registrar tiempo promedio para crear un pedido por voz | Alta | 2h |
| S5-013 | Registrar tasa de éxito del NLP (pedidos interpretados correctamente / total) | Alta | 1h |
| S5-014 | Registrar tasa de éxito del reconocimiento de voz (texto correcto / total dictados) | Alta | 1h |
| S5-015 | Registrar cantidad de correcciones manuales necesarias por método de entrada | Media | 1h |
| S5-016 | Registrar cantidad de pedidos confirmados vs cancelados | Media | 1h |
| S5-017 | Registrar tiempos de respuesta del backend (promedio, máximo) | Media | 2h |
| S5-018 | Comparar tiempos: pedido manual vs texto NLP vs voz | Alta | 2h |

---

## Épica 3: Análisis de aceptación del producto

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S5-019 | Tabular resultados de encuestas de clientes (promedios por pregunta) | Alta | 3h |
| S5-020 | Tabular resultados de encuestas de empresa AJE | Alta | 2h |
| S5-021 | Crear gráficos de barras con promedios de satisfacción por categoría | Alta | 3h |
| S5-022 | Crear gráfico de preferencia de método de entrada (texto/voz/manual) | Alta | 2h |
| S5-023 | Calcular Net Promoter Score (NPS) basado en recomendación | Alta | 2h |
| S5-024 | Calcular porcentaje de usuarios que usarían la app en producción | Alta | 1h |
| S5-025 | Analizar respuestas de texto libre (patrones, sugerencias recurrentes) | Alta | 3h |
| S5-026 | Comparar aceptación del sistema vs proceso manual actual | Alta | 2h |
| S5-027 | Identificar fortalezas principales del producto según usuarios | Alta | 2h |
| S5-028 | Identificar debilidades y áreas de mejora según usuarios | Alta | 2h |

---

## Épica 4: Reporte de efectividad del NLP y voz

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S5-029 | Crear tabla resumen de precisión del NLP (productos, cantidades, fechas) | Alta | 2h |
| S5-030 | Crear tabla resumen de precisión del reconocimiento de voz | Alta | 2h |
| S5-031 | Analizar tipos de errores más frecuentes del NLP | Alta | 2h |
| S5-032 | Analizar factores que afectan la calidad del reconocimiento de voz | Alta | 2h |
| S5-033 | Crear gráfico comparativo: pedido manual vs NLP vs voz (tiempo, precisión, satisfacción) | Alta | 3h |
| S5-034 | Documentar recomendaciones para mejorar NLP y voz en futuras versiones | Media | 2h |

---

## Épica 5: Informe ejecutivo para la stakeholder

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S5-035 | Redactar resumen ejecutivo del proyecto (1-2 páginas) | Alta | 3h |
| S5-036 | Incluir tabla de objetivos cumplidos vs no cumplidos | Alta | 2h |
| S5-037 | Incluir métricas clave de aceptación del producto | Alta | 2h |
| S5-038 | Incluir resultados principales de las encuestas | Alta | 2h |
| S5-039 | Incluir análisis de viabilidad del producto para producción | Media | 2h |
| S5-040 | Incluir recomendaciones para fases futuras del proyecto | Media | 2h |
| S5-041 | Incluir lecciones aprendidas del equipo | Media | 2h |
| S5-042 | Revisar y aprobar el informe con todo el equipo | Alta | 2h |

---

## Épica 6: Presentación final

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S5-043 | Crear presentación de diapositivas (mínimo 20 slides) | Alta | 6h |
| S5-044 | Incluir: introducción, problema, solución, arquitectura | Alta | — |
| S5-045 | Incluir: demo del sistema (capturas de pantalla y/o video) | Alta | — |
| S5-046 | Incluir: resultados de pruebas y métricas de aceptación | Alta | — |
| S5-047 | Incluir: conclusiones y recomendaciones | Alta | — |
| S5-048 | Crear video demostrativo del sistema (3-5 minutos) | Alta | 5h |
| S5-049 | Grabar flujo completo: registro → tienda → pedido por texto → confirmación | Alta | — |
| S5-050 | Grabar flujo completo: pedido por voz → corrección → confirmación | Alta | — |
| S5-051 | Grabar panel AJE: gestión de pedidos y cambio de estado | Alta | — |
| S5-052 | Ensayar presentación (al menos 2 ensayos) | Alta | 4h |
| S5-053 | Preparar respuestas a preguntas frecuentes de la stakeholder | Media | 2h |

---

## Épica 7: Documentación técnica final

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S5-054 | Actualizar README.md principal con estado final del proyecto | Alta | 2h |
| S5-055 | Documentar instrucciones de instalación y despliegue actualizadas | Alta | 2h |
| S5-056 | Documentar la API del backend (endpoints, parámetros, respuestas) | Alta | 3h |
| S5-057 | Documentar el motor NLP (cómo funciona, limitaciones, mejoras posibles) | Alta | 2h |
| S5-058 | Documentar la integración de reconocimiento de voz | Alta | 2h |
| S5-059 | Crear diagrama de arquitectura final del sistema | Alta | 2h |
| S5-060 | Crear diagrama de base de datos final (ER) | Alta | 2h |
| S5-061 | Asegurar que todo el código esté documentado con comentarios | Media | 3h |

---

## Resumen de estimaciones

| Épica | Tareas | Horas estimadas |
|---|---|---|
| Encuestas de satisfacción | 8 | 19h |
| Métricas de uso | 10 | 15h |
| Análisis de aceptación | 10 | 22h |
| Efectividad NLP/voz | 6 | 13h |
| Informe ejecutivo | 8 | 17h |
| Presentación final | 11 | 17h |
| Documentación técnica | 8 | 18h |
| **TOTAL** | **61** | **~121h** |
