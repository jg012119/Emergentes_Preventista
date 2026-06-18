# JMGR- Correcciones de la presentación — Preventista Inteligente AJE

## 1. Objetivo de la corrección

Transformar la presentación HTML actual en un **pitch comercial dirigido a la ingeniera y orientado a vender la propuesta a AJE**.

La presentación no debe sentirse como una exposición académica, un informe técnico ni una propuesta para sustituir a los preventistas. Debe mostrar que la solución funciona como un **canal digital complementario** que ayuda a AJE a recibir pedidos con menos fricción, atender reposiciones fuera de la visita programada y obtener mayor trazabilidad comercial.

La idea central que debe quedar en la mente de la audiencia es:

> **El Preventista Inteligente permite que las tiendas realicen pedidos por voz o chat cuando lo necesiten, mientras AJE mantiene el control de productos, clientes, pedidos y estados desde un panel centralizado.**

---

## 2. Instrucción principal para la IA que modificará el HTML

Corrige el archivo HTML actual de la presentación aplicando todas las instrucciones de este documento.

### Reglas obligatorias

1. Mantener el formato de presentación web, la navegación entre diapositivas, las animaciones y el simulador interactivo.
2. Conservar el diseño corporativo general, pero reducir la cantidad de texto por diapositiva.
3. Utilizar un lenguaje comercial, directo, profesional y creíble.
4. Hablar de los beneficios para AJE antes que de las tecnologías utilizadas.
5. No inventar porcentajes, costos, ahorros, tasas de error, niveles de adopción ni resultados.
6. Toda métrica debe cumplir al menos una de estas condiciones:
   - Proviene de una prueba real documentada.
   - Está claramente identificada como simulación.
   - Se presenta como indicador que será medido durante el piloto.
7. No presentar la solución como reemplazo de la fuerza de ventas.
8. No utilizar expresiones absolutas como “garantizado”, “elimina el 100%”, “duplica”, “costo cero” o “rentabilidad inmediata”.
9. No mencionar marcas competidoras dentro de ejemplos dirigidos a AJE.
10. Mantener la arquitectura técnica detallada únicamente como anexo o diapositiva de respaldo.
11. Incorporar una llamada a la acción clara: **autorizar o evaluar un piloto controlado**.
12. No modificar las funcionalidades reales del sistema ni agregar módulos inexistentes.

---

## 3. Correcciones críticas detectadas

### 3.1. Eliminar afirmaciones que no están respaldadas

Eliminar o reescribir las siguientes frases del HTML:

- “Duplica tu Cobertura de Ventas con IA”.
- “Reduce costos operativos de Bs. 15.00 a Bs. 0.50 por pedido”.
- “La preventa tradicional genera sobrecostos insostenibles”.
- “Hasta un 15% de devoluciones”.
- “Eliminando el 100% de errores de transcripción”.
- “Costo cero de licenciamiento”.
- “Absorbe más del 85% del tráfico”, salvo que exista evidencia técnica documentada.
- “Garantía de adopción y robustez”.
- “Resultados del piloto con tenderos reales”, si las personas evaluadas no fueron tenderos reales.
- “Rentabilidad inmediata”.
- “Ahorro mensual proyectado de Bs. 29.000”, si no proviene de datos entregados por AJE.
- “1.000 horas ahorradas”, si no existe un cálculo validado.
- “Prueba piloto costo cero”, si no se ha autorizado formalmente ofrecerla en esas condiciones.

Estas frases deben ser sustituidas por formulaciones prudentes como:

- “Potencial para ampliar la disponibilidad del canal de pedidos”.
- “Oportunidad de reducir tareas manuales y errores de registro”.
- “Impacto que será medido durante el piloto”.
- “Simulación basada en supuestos configurables”.
- “Arquitectura con componentes de código abierto”.

### 3.2. Corregir productos y marcas

En el mockup actual aparece:

> “Quiero 4 Coca-Colas y 2 paquetes de Bolt para el viernes”.

Debe cambiarse por un ejemplo compuesto únicamente por productos del catálogo real configurado para la demostración. Como mínimo:

- No mencionar Coca-Cola porque es una marca competidora.
- Corregir “Bolt” por “Volt” únicamente si Volt existe en el catálogo cargado.
- No inventar presentaciones, sabores o tamaños.

Ejemplo seguro:

> “Quiero 4 Big Cola de 2 litros y 2 Volt para el viernes”.

Antes de usar este ejemplo, validar que ambos productos existan en la base de datos de demostración.

### 3.3. Evitar la idea de sustitución laboral

Eliminar expresiones que indiquen que la IA reemplazará al preventista o absorberá completamente su trabajo.

Reemplazar por:

> “El canal digital complementa la visita del preventista y atiende solicitudes de reposición entre visitas, mientras el equipo comercial puede concentrarse en la relación con el cliente, la ejecución en el punto de venta y la apertura de nuevas oportunidades.”

### 3.4. Corregir el uso de “validación científica”

UNIVALLE puede presentarse como contexto académico o respaldo metodológico, pero no como “validación científica” sin un estudio formal, metodología aprobada y resultados verificables.

Reemplazar:

> “Respaldo y Validación Científica: UNIVALLE”.

Por:

> “Proyecto desarrollado en el marco académico de UNIVALLE”.

### 3.5. Corregir interpretación de usabilidad

No llamar “Bueno/Aceptable” a una puntuación SUS global de 58,6 sin explicar el criterio utilizado. Una puntuación de ese nivel demuestra que todavía existen oportunidades de mejora.

Presentar los resultados de manera transparente:

- Número de participantes.
- Perfil real de los participantes.
- Tareas evaluadas.
- Tasa de finalización.
- Tiempo promedio.
- Puntuación SUS.
- Limitaciones de la prueba.

No usar “Grado A”, “Excelente”, “Grado F” u otras clasificaciones si no se cita la escala utilizada.

---

# 4. Nueva estructura de la presentación

La presentación debe quedar organizada en **9 diapositivas principales** y una diapositiva técnica opcional como anexo.

---

## DIAPOSITIVA 1 — Propuesta de valor

### Título

**Pedidos más simples para las tiendas. Mayor visibilidad comercial para AJE.**

### Subtítulo

**Preventista Inteligente AJE**

Canal digital de pedidos por voz y chat que complementa el trabajo del preventista y centraliza la información operativa.

### Pie de página

Proyecto desarrollado en el marco académico de **UNIVALLE**  
Grupo 315 WHISPER: Luz E. Hinojosa, Jairo Guzmán y Valentina Trigo.

### Cambios visuales

- Mantener el nombre del proyecto y el mockup principal.
- Eliminar cifras de ahorro y promesas de duplicación.
- La portada debe comunicar una sola idea.

### Mensaje oral sugerido

> “Nuestra propuesta no busca reemplazar al preventista. Busca extender su capacidad de atención, permitiendo que las tiendas realicen reposiciones cuando las necesiten y que AJE conserve el control de cada pedido.”

---

## DIAPOSITIVA 2 — La oportunidad comercial

### Título

**La necesidad de reposición no siempre coincide con la visita programada**

### Subtítulo

El canal presencial es fundamental, pero puede complementarse con una alternativa digital disponible entre visitas.

### Presentar tres situaciones

#### 1. Pedidos entre visitas

Una tienda puede necesitar reposición antes de la siguiente visita del preventista.

#### 2. Registro manual o disperso

Los pedidos enviados por diferentes medios pueden requerir validación y transcripción adicional.

#### 3. Visibilidad operativa limitada

Sin un canal centralizado, el seguimiento de solicitudes, estados y productos puede demandar más coordinación.

### No utilizar

- Costos inventados por visita.
- Porcentajes de devoluciones no documentados.
- Lenguaje que critique agresivamente el proceso actual de AJE.

### Mensaje oral sugerido

> “Identificamos una oportunidad para complementar el canal actual, especialmente cuando una tienda necesita reponer producto fuera del recorrido programado.”

---

## DIAPOSITIVA 3 — La solución

### Título

**Un asistente digital de preventa disponible cuando la tienda lo necesita**

### Subtítulo

La tienda realiza su pedido por voz o chat; el sistema interpreta la solicitud, valida el catálogo y genera un borrador para confirmación.

### Beneficios funcionales

#### Pedido conversacional

El usuario puede escribir o dictar su solicitud utilizando expresiones cotidianas.

#### Validación antes de confirmar

El sistema presenta productos, cantidades y total para que el usuario revise el pedido.

#### Información centralizada

Los pedidos confirmados quedan disponibles para seguimiento desde el panel administrativo.

### Reemplazos necesarios

- Cambiar “Preventista de Bolsillo 24/7” por “Asistente digital de preventa”.
- Cambiar “Precisión garantizada” por “Confirmación previa del pedido”.
- Cambiar “elimina el 100% de errores” por “reduce el riesgo de errores de transcripción mediante confirmación”.

---

## DIAPOSITIVA 4 — Demostración del flujo

### Título

**Realizar un pedido puede ser tan sencillo como enviar un audio**

### Subtítulo

Demostración del recorrido completo desde la solicitud hasta la confirmación.

### Flujo visible

1. La tienda dicta o escribe su pedido.
2. El sistema reconoce productos y cantidades.
3. Se genera un borrador.
4. El usuario revisa la información.
5. El pedido se confirma y queda registrado.

### Instrucciones para el simulador

- Mantener el simulador interactivo.
- Utilizar productos reales del catálogo de demostración.
- Mostrar al menos tres escenarios:
  - Pedido claro reconocido por reglas.
  - Expresión coloquial interpretada por el modelo local.
  - Producto fuera del catálogo rechazado correctamente.
- Cambiar etiquetas muy técnicas como “LLaMA 3.1” o “NLP Reglas” por nombres comprensibles para la audiencia:
  - “Reconocimiento directo”.
  - “Interpretación contextual”.
  - “Validación del catálogo”.
- Los detalles tecnológicos pueden mostrarse en pequeño o explicarse durante preguntas.

### Mensaje oral sugerido

> “La inteligencia no está solamente en entender el audio; está en convertirlo en un pedido verificable antes de enviarlo.”

---

## DIAPOSITIVA 5 — Valor para AJE

### Título

**Una solución con beneficios para cada actor del proceso**

### Subtítulo

El sistema conecta la necesidad de la tienda con la operación comercial de AJE.

### Distribución sugerida en tres columnas

#### Para la tienda

- Solicitud de reposición sin esperar la siguiente visita.
- Confirmación clara de cantidades y productos.
- Consulta del estado de sus pedidos.

#### Para el preventista

- Menos tareas repetitivas de transcripción.
- Mayor contexto antes de visitar al cliente.
- Más tiempo para negociación, relación comercial y ejecución en tienda.

#### Para AJE

- Pedidos centralizados.
- Seguimiento de estados.
- Historial por cliente.
- Información para evaluar demanda y operación.

### Sustituye a la diapositiva técnica principal

La arquitectura detallada actual no debe ocupar una diapositiva central del pitch. El valor comercial debe aparecer antes que el stack tecnológico.

---

## DIAPOSITIVA 6 — Control operativo

### Título

**Cada pedido queda visible y gestionable desde un solo panel**

### Subtítulo

La consola administrativa permite revisar pedidos, clientes, productos y estados desde una fuente centralizada.

### Funciones que pueden mostrarse

- Resumen de pedidos.
- Pedidos pendientes, confirmados o rechazados.
- Información del cliente.
- Detalle de productos y cantidades.
- Actualización del estado.
- Historial y reportes básicos.

### Reescritura de beneficios

Cambiar “Control Total de la Demanda” por “Visibilidad operativa de los pedidos”.

Evitar afirmar que las métricas son “en tiempo real” si técnicamente se actualizan solamente cuando se recarga o consulta la información.

### Mensaje oral sugerido

> “La tienda obtiene simplicidad; AJE mantiene control. Todo pedido generado desde el asistente llega a una consola donde puede ser revisado y gestionado.”

---

## DIAPOSITIVA 7 — Validación realizada

### Título

**Probamos el sistema, identificamos fricciones y aplicamos mejoras**

### Subtítulo

La evaluación permitió medir la facilidad de uso y corregir problemas antes de proponer un piloto operativo.

### Mostrar únicamente datos comprobables

Si los resultados de 33 participantes están respaldados por el informe real, presentar:

- **33 participantes evaluados.**
- **89,2 % de tareas completadas**, indicando qué tareas fueron medidas.
- **92,4 segundos por pedido**, indicando si es promedio o mediana.
- **SUS de 58,6/100**, presentado como resultado con oportunidades de mejora.

### Agregar una nota de alcance

> “La muestra corresponde a una validación académica de usabilidad. Los resultados no representan todavía una validación comercial con la red de tiendas de AJE.”

### Hallazgos resumidos

No mostrar cinco tarjetas extensas. Reducir a tres aprendizajes:

1. **Reconocimiento local:** configuración de español de Bolivia para mejorar la captura de voz.
2. **Tolerancia a errores:** emparejamiento aproximado para nombres de productos escritos de distintas formas.
3. **Claridad de interacción:** mejoras en carga, formularios y confirmación visual del pedido.

### Condición

Si los 33 participantes, los porcentajes o los tiempos no pueden verificarse, reemplazar toda la diapositiva por una **validación funcional** sin cifras inventadas.

---

## DIAPOSITIVA 8 — Propuesta de piloto

### Título

**El siguiente paso es medir el impacto en una ruta real**

### Subtítulo

Proponemos una prueba controlada para comparar el proceso actual con el canal digital complementario.

### Diseño recomendado

Reemplazar la calculadora de “ROI inmediato” por una propuesta de piloto con tres fases.

#### Fase 1. Preparación

- Selección de tiendas participantes.
- Configuración del catálogo y usuarios.
- Definición de línea base e indicadores.

#### Fase 2. Ejecución

- Uso del asistente por voz y chat.
- Seguimiento de pedidos y errores.
- Acompañamiento a usuarios.

#### Fase 3. Evaluación

- Comparación de resultados.
- Identificación de mejoras.
- Decisión sobre una siguiente etapa.

### Indicadores del piloto

- Tiempo promedio para registrar un pedido.
- Tasa de pedidos completados.
- Errores o correcciones antes de confirmar.
- Pedidos realizados fuera de la visita programada.
- Adopción por parte de las tiendas.
- Valor promedio y frecuencia de pedido.
- Satisfacción de usuarios y operadores.

### Regla sobre el ROI

No mostrar ahorro monetario hasta contar con datos reales de AJE.

Si se conserva una calculadora, debe llamarse:

> **Simulador de impacto potencial**

Y debe mostrar de forma visible todos sus supuestos, indicando:

> “Los valores son referenciales y deben validarse con información operativa de AJE.”

---

## DIAPOSITIVA 9 — Cierre comercial

### Título

**Validemos juntos una nueva forma de recibir pedidos**

### Mensaje central

> “El Preventista Inteligente no reemplaza la relación comercial. La fortalece con un canal adicional, disponible, trazable y fácil de utilizar.”

### Llamada a la acción

**Propuesta:** revisar la solución con el equipo responsable y definir el alcance de un piloto controlado.

### Pasos mostrados

1. Validar el flujo con AJE.
2. Seleccionar una muestra de tiendas o ruta.
3. Medir resultados y decidir la siguiente fase.

### Equipo

Mostrar los integrantes de forma secundaria, en una franja inferior:

- Luz Esmeralda Hinojosa Laredo — Frontend y experiencia móvil.
- Jairo Guzmán — Backend e interpretación inteligente.
- Valentina Trigo — Producto y base de datos.

### Eliminar

- Formulario de contacto ficticio.
- Correo corporativo no confirmado.
- Botón que simula una reunión agendada.
- Frase “socios estratégicos de AJE” si no existe una relación formal.
- Compromisos no autorizados sobre duración, cantidad de tiendas o costo del piloto.

---

# 5. Diapositiva técnica opcional — Anexo

## Título

**Arquitectura preparada para validación y crecimiento**

Esta diapositiva solo debe mostrarse si la ingeniera pregunta por la implementación.

### Contenido resumido

- Aplicación móvil para pedidos por voz y chat.
- Backend en FastAPI.
- Procesamiento híbrido mediante reglas y modelo local.
- Base de datos centralizada en Supabase.
- Panel web para administración.
- Autenticación y control de acceso.

### No mostrar en el pitch principal

- Cantidad de líneas de código.
- Nombres de archivos internos.
- Temperatura del modelo.
- Timeout específico.
- Detalles de Levenshtein, JSON schemas o estructura del repositorio.

Estos elementos pueden incluirse en documentación técnica, no en el discurso comercial principal.

---

# 6. Reglas de redacción

## Usar

- “Permite”.
- “Facilita”.
- “Ayuda a reducir”.
- “Complementa”.
- “Centraliza”.
- “Hace visible”.
- “Potencial de mejora”.
- “Propuesta de piloto”.
- “Indicadores por validar”.

## Evitar

- “Garantiza”.
- “Elimina completamente”.
- “Duplica”.
- “Costo cero”.
- “Rentabilidad inmediata”.
- “Reemplaza”.
- “Control total”.
- “Validación científica”.
- “Mercado validado”, si no hubo validación comercial real.

---

# 7. Reglas visuales

1. Mantener una idea principal por diapositiva.
2. Limitar cada tarjeta a un título y un máximo de dos líneas de explicación.
3. Evitar párrafos de más de 45 palabras.
4. Priorizar capturas y flujos visuales sobre texto técnico.
5. Utilizar cifras grandes únicamente cuando sean reales y verificables.
6. Diferenciar visualmente:
   - Problema u oportunidad.
   - Solución.
   - Evidencia.
   - Propuesta de piloto.
7. Mantener contraste alto y legibilidad en proyector.
8. Verificar la vista móvil y resoluciones de presentación 16:9.
9. No utilizar íconos o elementos interactivos que parezcan funcionales si no realizan una acción útil.
10. No saturar la presentación con gradientes, tarjetas o animaciones simultáneas.

---

# 8. Orden narrativo obligatorio

La historia debe avanzar así:

> **Oportunidad actual → solución → funcionamiento → valor para AJE → control operativo → evidencia → piloto → decisión solicitada.**

No comenzar explicando frameworks, arquitectura o inteligencia artificial. La IA es un medio; el valor comercial es el mensaje principal.

---

# 9. Lista de búsqueda y reemplazo dentro del HTML

Buscar todas las apariciones y corregirlas:

| Texto actual | Sustitución recomendada |
|---|---|
| Duplica tu Cobertura de Ventas con IA | Pedidos más simples para las tiendas. Mayor visibilidad comercial para AJE. |
| Reduce costos operativos de Bs. 15.00 a Bs. 0.50 por pedido | Centraliza pedidos por voz y chat en un canal digital complementario. |
| Respaldo y Validación Científica: UNIVALLE | Proyecto desarrollado en el marco académico de UNIVALLE |
| ¿Cuánto cuesta no digitalizar? | La necesidad de reposición no siempre coincide con la visita programada |
| sobrecostos operativos insostenibles | oportunidades de mejora y coordinación operativa |
| El Preventista de Bolsillo 24/7 | Un asistente digital de preventa |
| Precisión Garantizada | Confirmación previa del pedido |
| eliminando el 100% de errores de transcripción | reduciendo el riesgo de errores mediante revisión y confirmación |
| Coca-Colas | Big Cola, validando previamente el catálogo |
| Bolt | Volt, solo si existe en el catálogo |
| Arquitectura a Costo Cero de Licenciamiento | Arquitectura preparada para validación y crecimiento |
| Control Total de la Demanda | Visibilidad operativa de los pedidos |
| Garantía de Adopción y Robustez | Validación, aprendizajes y mejoras |
| Rentabilidad Inmediata (ROI) | Propuesta de piloto e indicadores de impacto |
| Iniciemos el Piloto en tus Rutas | Validemos juntos una nueva forma de recibir pedidos |
| Socios estratégicos en la digitalización de AJE Bolivia | Equipo desarrollador de la propuesta |

---

# 10. Criterios de aceptación

La corrección se considerará terminada cuando:

- [ ] La presentación tenga nueve diapositivas principales.
- [ ] La propuesta de valor sea comprensible en menos de 20 segundos.
- [ ] No aparezca ninguna marca competidora en los pedidos de ejemplo.
- [ ] No existan cifras comerciales sin fuente o sin etiqueta de simulación.
- [ ] La solución se presente como complemento del preventista.
- [ ] El stack tecnológico no sea el centro del pitch.
- [ ] La demostración utilice el catálogo real del proyecto.
- [ ] Los resultados de usabilidad estén explicados sin exageración.
- [ ] La calculadora de ROI haya sido eliminada o convertida en simulador con supuestos visibles.
- [ ] El cierre solicite una acción concreta.
- [ ] No se muestren correos, cargos o compromisos no confirmados.
- [ ] La presentación conserve navegación, animaciones y adaptación responsive.
- [ ] El HTML, CSS y JavaScript no generen errores en consola.

---

# 11. Resultado esperado

La presentación final debe lograr que la ingeniera piense:

> “La solución entiende una necesidad real del canal de preventa, ya tiene un prototipo funcional y propone una manera prudente de comprobar su valor con AJE.”

No debe dar la impresión de que el equipo está prometiendo resultados financieros que todavía no ha demostrado.
