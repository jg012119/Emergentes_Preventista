# 📦 Sprint 3 — Entregables

## Entregable principal

**App móvil con reconocimiento de voz integrado**, que permite al cliente dictar pedidos y enviarlos al NLP para generar extractos automáticos.

---

## Lista de entregables

### 1. Hook de reconocimiento de voz

- `useVoiceRecognition` implementado con:
  - Inicio/parada de reconocimiento.
  - Resultados parciales y finales.
  - Manejo de errores.
  - Configuración de idioma español.

### 2. UI de grabación de voz

- Botón de micrófono con estados visuales (inactivo/grabando/procesando).
- Animación de onda o pulso durante la grabación.
- Indicadores de texto ("Escuchando...", "Procesando...").
- Campo de texto editable para corrección.
- Botón de enviar y botón de regrabar.

### 3. Flujo completo integrado

- Voz → Texto reconocido → Campo editable → NLP → Extracto → Confirmación → Pedido.
- El flujo reutiliza la infraestructura NLP del Sprint 2.
- La experiencia es fluida y sin interrupciones.

### 4. Documentación de pruebas de voz

- Documento con resultados de pruebas en dispositivo real.
- Evaluación de reconocimiento en diferentes condiciones.
- Registro de errores encontrados y correcciones aplicadas.

---

## Evidencias requeridas

| Evidencia | Descripción |
|---|---|
| Video / GIF | Dictado de pedido por voz en dispositivo real |
| Captura de pantalla | Botón de micrófono en estado "grabando" |
| Captura de pantalla | Texto reconocido en campo editable |
| Captura de pantalla | Extracto generado desde el texto dictado |
| Captura de pantalla | Pedido confirmado desde dictado por voz |
| Captura de pantalla | Mensaje de error por permisos denegados |
| Captura de pantalla | Mensaje de error por voz no detectada |
| Documento | Resultados de pruebas de voz |

---

## Definición de "Done"

- [x] `@react-native-voice/voice` integrado y funcional.
- [x] Permisos de micrófono configurados (Android/iOS).
- [x] UI de grabación implementada con estados visuales.
- [x] Corrección manual del texto funcional.
- [x] Flujo completo voz → NLP → extracto → confirmación verificado.
- [x] Pruebas en dispositivo real documentadas.
- [x] Código subido al repositorio.
