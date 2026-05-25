# 📦 Sprint 4 — Entregables

## Entregable principal

**Sistema probado y estabilizado**, con documentación completa de pruebas y errores corregidos.

---

## Lista de entregables

### 1. Informe de pruebas unitarias

- Resultados de al menos 10 tests unitarios del backend.
- Cobertura de casos exitosos y de error.
- Porcentaje de tests que pasan.

### 2. Informe de pruebas de integración

- Resultados de los 4 flujos principales probados end-to-end:
  1. Registro → Login → Tienda → Pedido manual → Confirmación.
  2. Chat escrito → NLP → Extracto → Confirmación.
  3. Voz → Texto → NLP → Extracto → Confirmación.
  4. Pedido → AJE cambia estado → Notificación.
- Capturas de pantalla de cada paso.

### 3. Informe de pruebas del NLP

- Tabla de casos probados con entrada, salida esperada y salida real.
- Tasa de precisión calculada.
- Análisis de casos fallidos.
- Recomendaciones de mejora.

### 4. Informe de pruebas de reconocimiento de voz

- Tabla de frases probadas con condiciones y resultados.
- Tasa de precisión en diferentes condiciones.
- Análisis de factores que afectan el reconocimiento.

### 5. Informe de pruebas de usabilidad

- Evaluación de cada flujo principal.
- Retroalimentación de usuarios de prueba.
- Hallazgos principales.
- Recomendaciones priorizadas.

### 6. Checklist de pruebas de aceptación

- Lista completa de los 20 criterios de aceptación.
- Estado de cumplimiento de cada criterio (✅ / ❌).
- Justificación de criterios no cumplidos.

### 7. Registro de errores (Bug tracker)

- Lista de todos los errores encontrados.
- Clasificación por severidad (Crítico, Alto, Medio, Bajo).
- Estado de corrección (Corregido, Pendiente, No se corregirá).
- Fecha de detección y corrección.

### 8. Sistema estabilizado

- Código fuente con todas las correcciones aplicadas.
- Pruebas de regresión ejecutadas y pasando.
- Sistema listo para presentación.

---

## Evidencias requeridas

| Evidencia | Descripción |
|---|---|
| Documento | Informe de pruebas unitarias |
| Documento | Informe de pruebas de integración |
| Documento | Informe de pruebas del NLP con tabla de precisión |
| Documento | Informe de pruebas de voz con tabla de precisión |
| Documento | Informe de pruebas de usabilidad |
| Documento | Checklist de pruebas de aceptación firmado |
| Documento | Registro de errores (bug tracker) |
| Capturas | Evidencia de flujos probados end-to-end |
| Terminal | Output de tests unitarios pasando |

---

## Definición de "Done"

- [x] Todos los tipos de pruebas ejecutados.
- [x] Errores críticos y altos corregidos.
- [x] Pruebas de regresión pasando.
- [x] Precisión NLP ≥ 80%.
- [x] Toda la documentación de pruebas completada.
- [x] Sistema estabilizado y listo para presentación.
- [x] Código actualizado en el repositorio.
