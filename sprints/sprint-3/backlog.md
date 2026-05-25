# 📝 Sprint 3 — Backlog de Tareas

## Épica 1: Integración de @react-native-voice/voice

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S3-001 | Instalar dependencia `@react-native-voice/voice` en el proyecto React Native | Alta | 1h |
| S3-002 | Configurar permisos de micrófono en `AndroidManifest.xml` (Android) | Alta | 1h |
| S3-003 | Configurar permisos de micrófono en `Info.plist` (iOS) | Alta | 1h |
| S3-004 | Crear hook personalizado `useVoiceRecognition` para encapsular la lógica de voz | Alta | 4h |
| S3-005 | Implementar inicio de reconocimiento de voz (`Voice.start('es-BO')`) | Alta | 2h |
| S3-006 | Implementar detención de reconocimiento de voz (`Voice.stop()`) | Alta | 1h |
| S3-007 | Capturar resultados parciales en tiempo real (`onSpeechPartialResults`) | Alta | 2h |
| S3-008 | Capturar resultado final del reconocimiento (`onSpeechResults`) | Alta | 2h |
| S3-009 | Manejar errores del reconocimiento (`onSpeechError`) | Alta | 2h |
| S3-010 | Configurar idioma de reconocimiento: `es-BO` con fallback a `es-ES` | Alta | 1h |

---

## Épica 2: Pantalla de dictado por voz

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S3-011 | Crear/modificar pantalla de chat para incluir botón de micrófono | Alta | 2h |
| S3-012 | Diseñar botón de grabación con estados visuales (inactivo, grabando, procesando) | Alta | 3h |
| S3-013 | Implementar animación de onda/pulso mientras se graba | Media | 3h |
| S3-014 | Mostrar texto reconocido en tiempo real mientras el usuario habla | Alta | 3h |
| S3-015 | Mostrar indicador de "Escuchando..." durante la grabación | Alta | 1h |
| S3-016 | Mostrar indicador de "Procesando..." después de detener la grabación | Media | 1h |
| S3-017 | Permitir cancelar la grabación sin enviar el texto | Media | 1h |

---

## Épica 3: Corrección manual del texto reconocido

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S3-018 | Como cliente, quiero ver el texto reconocido antes de enviarlo al sistema | Alta | 2h |
| S3-019 | Como cliente, quiero poder editar el texto reconocido antes de enviarlo | Alta | 3h |
| S3-020 | Como cliente, quiero poder regrabar si el reconocimiento fue incorrecto | Alta | 2h |
| S3-021 | Implementar campo de texto editable que muestra el resultado del reconocimiento | Alta | 2h |
| S3-022 | Agregar botón "Enviar" para enviar el texto (original o corregido) al NLP | Alta | 1h |

---

## Épica 4: Conexión voz → NLP → extracto

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S3-023 | Enviar texto reconocido (o corregido) al endpoint `POST /nlp/parse-order` | Alta | 2h |
| S3-024 | Mostrar extracto generado desde el texto dictado en el chat | Alta | 2h |
| S3-025 | Implementar flujo de confirmación después del dictado por voz | Alta | 2h |
| S3-026 | El flujo de voz → texto → NLP → extracto → confirmación debe funcionar end-to-end | Alta | 3h |

---

## Épica 5: Manejo de errores de voz

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S3-027 | Mostrar mensaje si el micrófono no está disponible o los permisos fueron denegados | Alta | 2h |
| S3-028 | Mostrar mensaje si no se detecta voz ("No escuché nada, intenta de nuevo") | Alta | 1h |
| S3-029 | Mostrar mensaje si hay error de conexión (el reconocimiento requiere internet) | Alta | 1h |
| S3-030 | Implementar timeout si el usuario no habla en 10 segundos | Media | 2h |
| S3-031 | Manejar caso de texto irreconocible o muy corto | Media | 1h |

---

## Épica 6: Pruebas de reconocimiento de voz

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S3-032 | Probar dictado: "Quiero 4 Coca-Colas y 2 paquetes de Bolt para el viernes" | Alta | 1h |
| S3-033 | Probar dictado en ambiente silencioso | Alta | 1h |
| S3-034 | Probar dictado en ambiente con ruido | Alta | 1h |
| S3-035 | Probar dictado con diferentes acentos (Bolivia) | Alta | 1h |
| S3-036 | Probar corrección manual del texto reconocido | Alta | 1h |
| S3-037 | Probar regrabación después de error | Alta | 1h |
| S3-038 | Probar flujo completo: voz → texto → NLP → extracto → confirmación → pedido | Alta | 2h |
| S3-039 | Probar permisos denegados de micrófono | Media | 1h |
| S3-040 | Documentar resultados de todas las pruebas de voz | Alta | 2h |

---

## Resumen de estimaciones

| Épica | Tareas | Horas estimadas |
|---|---|---|
| Integración voice | 10 | 17h |
| Pantalla de dictado | 7 | 14h |
| Corrección manual | 5 | 10h |
| Conexión voz → NLP | 4 | 9h |
| Manejo de errores | 5 | 7h |
| Pruebas de voz | 9 | 11h |
| **TOTAL** | **40** | **~68h** |
