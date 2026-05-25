# ✅ Sprint 3 — Criterios de Aceptación

## Reconocimiento de voz

- [ ] La app solicita permisos de micrófono al usuario (Android/iOS).
- [ ] El botón de micrófono inicia la captura de audio.
- [ ] El texto reconocido se muestra en tiempo real mientras el usuario habla.
- [ ] Al detener la grabación, el texto final se muestra en un campo editable.
- [ ] El idioma de reconocimiento está configurado en español (es-BO o es-ES).

---

## Corrección manual

- [ ] El cliente puede ver el texto reconocido antes de enviarlo.
- [ ] El cliente puede editar/corregir el texto reconocido en un campo de texto.
- [ ] El cliente puede regrabar si el reconocimiento fue incorrecto.
- [ ] El botón "Enviar" envía el texto (original o corregido) al endpoint NLP.

---

## Flujo completo voz → pedido

- [ ] El cliente dicta: "Quiero 4 Coca-Colas y 2 paquetes de Bolt para el viernes".
- [ ] El sistema convierte la voz a texto.
- [ ] El texto se envía al endpoint NLP.
- [ ] El sistema genera el extracto del pedido.
- [ ] El extracto se muestra en el chat.
- [ ] El cliente confirma el pedido.
- [ ] El pedido se guarda en estado Pendiente con los datos correctos.

---

## Indicadores visuales

- [ ] El botón de micrófono muestra estado "inactivo" por defecto.
- [ ] El botón cambia a estado "grabando" con indicador visual (onda/pulso).
- [ ] Se muestra "Escuchando..." durante la grabación.
- [ ] Se muestra "Procesando..." después de detener la grabación.

---

## Manejo de errores

- [ ] Si los permisos de micrófono son denegados, se muestra un mensaje claro.
- [ ] Si no se detecta voz, se muestra "No escuché nada, intenta de nuevo".
- [ ] Si hay error de conexión, se informa al usuario.
- [ ] Si el texto es muy corto o irreconocible, se pide al usuario que repita.
- [ ] La grabación se detiene automáticamente después de 10 segundos de silencio.

---

## Pruebas en dispositivos reales

- [ ] El reconocimiento funciona en al menos un dispositivo Android real.
- [ ] El reconocimiento funciona en ambiente silencioso.
- [ ] El reconocimiento se probó en ambiente con ruido moderado.
- [ ] La corrección manual funciona correctamente.
- [ ] El flujo completo fue probado end-to-end en un dispositivo real.

---

## Criterio global de completitud

> **El Sprint 3 se considera completo cuando el cliente puede dictar un pedido por voz en la app, ver el texto reconocido, corregirlo si es necesario, enviarlo al NLP, ver el extracto generado y confirmar el pedido para crearlo en el sistema.**
