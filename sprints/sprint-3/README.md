# 🎤 Sprint 3 — Reconocimiento de Voz

## Objetivo

Implementar el **reconocimiento de voz** en la app móvil usando `@react-native-voice/voice`, permitiendo que el cliente **dicte su pedido** y el sistema convierta la voz en texto para procesarlo con el motor NLP existente (Sprint 2).

---

## Alcance del sprint

### ✅ Incluido

- **Integración de `@react-native-voice/voice`** en la app React Native.
- **Solicitud de permisos** de micrófono (Android/iOS).
- **Captura de audio** del usuario con botón de grabación.
- **Conversión de voz a texto** en tiempo real (speech-to-text).
- **Envío del texto reconocido** al endpoint NLP (`POST /nlp/parse-order`).
- **Corrección manual** del texto antes de procesar.
- **Indicadores visuales** de estado de grabación (grabando, procesando, listo).
- **Manejo de errores** de reconocimiento de voz.

### ❌ Excluido

- Entrenamiento de modelos de voz propios.
- Reconocimiento offline completo.
- Soporte multiidioma (solo español).

---

## Responsables

| Componente | Responsable | Apoyo |
|---|---|---|
| Integración @react-native-voice/voice | Valentina Trigo | Jairo |
| UI de grabación de voz | Valentina Trigo | Luz |
| Corrección manual de texto | Luz Laredo | Valentina |
| Pruebas en dispositivos reales | Todo el equipo | — |

---

## Duración estimada

**1 semana**

---

## Dependencias

- Sprint 2 completado (motor NLP funcional).
- App móvil con chat integrado al NLP.
- Dispositivo Android o iOS real para pruebas de micrófono.

---

## Notas técnicas

- `@react-native-voice/voice` usa los motores nativos del dispositivo (Google Speech / Apple Speech).
- El reconocimiento depende de la conexión a internet en la mayoría de dispositivos.
- **Siempre** se debe permitir corrección manual del texto reconocido antes de enviarlo.
- Se recomienda probar en ambiente silencioso y con ruido para evaluar calidad.
- El idioma debe configurarse como `es-BO` (español Bolivia) o `es-ES` como fallback.
