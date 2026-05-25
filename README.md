# AGENTE INTELIGENTE DE PROCESAMIENTO DE LENGUAJE NATURAL PARA LA RECEPCIÓN Y GESTIÓN DE PEDIDOS

## 1. Datos generales del proyecto

**Grupo / Identificador:** 315 WHISPER  
**Empresa de referencia:** AJE  
**Stakeholder / Cliente final:** Ing. Claudia Ureña Hinojosa  

### Integrantes

- Luz Laredo
- Jairo Guzman
- Valentina Trigo

---

## 2. Tema

Desarrollo de un MVP de preventista inteligente para que tiendas, supermercados o mayoristas puedan realizar pedidos a la empresa AJE mediante lenguaje natural escrito o por voz.

El sistema permitirá que el cliente registre su tienda, indique su ubicación, escriba o dicte un pedido, confirme el extracto generado por el sistema y posteriormente reciba la actualización del estado de su pedido por chat y correo electrónico.

---

## 3. Descripción del proyecto

El proyecto consiste en una aplicación móvil y un panel web/tablet para la recepción y gestión de pedidos comerciales.

El usuario podrá realizar un pedido usando lenguaje natural, por ejemplo:

> "Quiero 4 Coca-Colas y 2 paquetes de Bolt para el viernes."

El sistema interpretará el mensaje y extraerá los datos importantes del pedido:

- Productos solicitados
- Cantidades
- Precio unitario
- Subtotal por producto
- Total del pedido
- Fecha de entrega
- Nombre de la tienda
- Dirección
- Ubicación
- Observaciones

Antes de enviar el pedido a la empresa, el sistema mostrará un extracto para que el usuario confirme. Solo después de la confirmación, el pedido será registrado en la base de datos con estado **Pendiente**.

Desde el panel de AJE, la empresa podrá revisar el pedido, validar disponibilidad de stock y cambiar el estado a:

- Pendiente
- Confirmado
- Rechazado
- En proceso

Cuando el estado cambie, el cliente recibirá una notificación en el mismo chat y también mediante correo electrónico.

---

## 4. Problema identificado

Actualmente, muchos pedidos comerciales entre preventistas, tiendas y empresas se realizan de forma manual, por llamadas, mensajes de WhatsApp o notas informales. Esto puede generar problemas como:

- Pedidos incompletos.
- Errores en cantidades.
- Falta de confirmación clara.
- Dificultad para controlar precios.
- Falta de control de stock.
- Pérdida de información.
- Mala trazabilidad del estado del pedido.
- Dependencia de una persona preventista para registrar cada solicitud.

El proyecto busca reducir estos problemas mediante una solución digital simple, rápida y entendible para el usuario final.

---

## 5. Objetivo principal

Construir un MVP funcional de preventista inteligente que automatice la recepción y gestión inicial de pedidos comerciales para AJE mediante lenguaje natural escrito o por voz.

---

## 6. Objetivos específicos

1. Desarrollar una aplicación móvil que permita registrar clientes, tiendas, ubicación y pedidos.
2. Implementar un chat de pedidos capaz de recibir texto escrito.
3. Incorporar reconocimiento de voz para convertir pedidos hablados en texto.
4. Procesar el lenguaje natural del usuario para extraer productos, cantidades, precios, fechas y observaciones.
5. Generar un extracto del pedido antes de enviarlo a la empresa.
6. Registrar pedidos confirmados en la base de datos.
7. Implementar un panel web/tablet para que AJE revise y gestione pedidos.
8. Incorporar control básico de stock y precios.
9. Notificar al cliente por chat y correo cuando el pedido cambie de estado.

---

## 7. Alcance funcional

El MVP incluirá las siguientes funcionalidades:

### Aplicación móvil del cliente

- Registro de usuario.
- Registro de tienda.
- Nombre de la tienda.
- Dirección de la tienda.
- Ubicación de la tienda.
- Chat para realizar pedidos.
- Entrada de pedidos por texto.
- Entrada de pedidos por voz.
- Generación de extracto previo.
- Confirmación manual del pedido.
- Historial de pedidos.
- Visualización del estado del pedido.
- Notificaciones dentro del chat.

### Panel web/tablet para AJE

- Login básico para la empresa.
- Listado de pedidos recibidos.
- Visualización del detalle del pedido.
- Validación de productos.
- Validación de precios.
- Validación de stock.
- Cambio de estado del pedido.
- Gestión básica de productos.
- Gestión básica de stock.
- Gestión básica de tiendas/clientes.

---

## 8. Fuera de alcance

Por el tiempo limitado del proyecto, no se incluirán las siguientes funciones:

- ERP completo.
- Facturación legal.
- Pagos en línea.
- Integración real con sistemas internos de AJE.
- Rutas de distribución.
- Aplicación para repartidores.
- Inteligencia artificial entrenada desde cero.
- Reconocimiento perfecto de todos los dialectos.
- Inventario avanzado.
- Gestión contable.
- Módulo de compras.
- Módulo de almacenes completo.
- Sistema de roles complejo.

---

## 9. Situaciones de uso

| Situación | Flujo mínimo | Resultado esperado |
|---|---|---|
| Pedido escrito | El cliente escribe su pedido en el chat | El sistema interpreta productos, cantidades, precios y fecha |
| Pedido por voz | El cliente dicta su pedido desde el micrófono | La app convierte la voz en texto y lo envía al backend |
| Confirmación previa | El sistema muestra un extracto del pedido | El cliente confirma o corrige antes de enviar |
| Registro de tienda | El cliente registra nombre, dirección y ubicación | El pedido queda asociado a una tienda real |
| Validación de AJE | La empresa revisa el pedido desde el panel | Se cambia el estado del pedido |
| Notificación | AJE confirma, rechaza o procesa el pedido | El cliente recibe aviso por chat y correo |
| Control de stock | El sistema compara cantidad solicitada con stock | Se evita confirmar pedidos sin disponibilidad suficiente |

---

## 10. Flujo general del sistema

```text
Cliente escribe o dicta pedido
        ↓
La app convierte voz a texto si corresponde
        ↓
El backend interpreta el texto
        ↓
Se extraen productos, cantidades, precios y fecha
        ↓
El sistema genera un extracto del pedido
        ↓
El cliente confirma o corrige
        ↓
El pedido se guarda en estado Pendiente
        ↓
AJE revisa desde el panel web/tablet
        ↓
AJE cambia el estado del pedido
        ↓
El cliente recibe notificación por chat y correo
```

---

## 11. Estados del pedido

| Estado | Descripción |
|---|---|
| Borrador | Pedido todavía no confirmado por el cliente |
| Pendiente | Pedido enviado y esperando revisión de AJE |
| Confirmado | Pedido aceptado por la empresa |
| Rechazado | Pedido no aceptado por falta de stock, error u otro motivo |
| En proceso | Pedido aceptado y en preparación |

---

## 12. Tecnologías acordadas

| Componente | Tecnología |
|---|---|
| Aplicación móvil | React Native |
| Reconocimiento de voz | @react-native-voice/voice |
| Backend | FastAPI |
| Lenguaje backend | Python |
| Base de datos | Supabase |
| Motor de base de datos | PostgreSQL administrado por Supabase |
| Panel web/tablet | React + Vite |
| Notificaciones | Chat interno + correo electrónico |
| Procesamiento de pedidos | Reglas de extracción de lenguaje natural |

---

## 13. Decisión sobre reconocimiento de voz

Inicialmente se consideró Whisper como tecnología de reconocimiento de voz. Sin embargo, para este MVP no se utilizará Whisper.

La alternativa seleccionada para la app móvil será:

**@react-native-voice/voice**

Esta opción es más coherente con React Native porque permite trabajar directamente con reconocimiento de voz dentro de aplicaciones móviles Android/iOS.

### Justificación

Se elige esta alternativa porque:

- Está orientada a aplicaciones móviles.
- Se integra con React Native.
- Permite convertir voz en texto.
- Es más viable para un MVP de corto plazo.
- Evita depender de un modelo pesado de transcripción.
- Permite hacer pruebas en dispositivos reales.

> **Nota importante:** El sistema siempre deberá permitir corrección manual del texto antes de enviar el pedido, porque el reconocimiento de voz puede fallar por ruido, acentos, mala pronunciación o errores del dispositivo.

---

## 14. Arquitectura propuesta

```text
┌────────────────────────────┐
│ App móvil React Native     │
│ Cliente / tienda           │
└──────────────┬─────────────┘
               │
               │ Pedido por texto o voz
               ↓
┌────────────────────────────┐
│ Backend FastAPI            │
│ Procesamiento del pedido   │
└──────────────┬─────────────┘
               │
               │ Guarda y consulta datos
               ↓
┌────────────────────────────┐
│ Supabase                   │
│ Base de datos PostgreSQL   │
└──────────────┬─────────────┘
               │
               │ Consulta pedidos
               ↓
┌────────────────────────────┐
│ Panel React + Vite         │
│ Empresa AJE                │
└────────────────────────────┘
```

---

## 15. Módulos del sistema

### Módulo 1: Clientes

Permite registrar los datos del usuario que realiza pedidos.

**Campos principales:**

- ID del cliente
- Nombre
- Teléfono
- Correo
- Contraseña
- Estado

### Módulo 2: Tiendas

Permite registrar la tienda desde donde se realizará el pedido.

**Campos principales:**

- ID de tienda
- ID del cliente
- Nombre de la tienda
- Dirección
- Ubicación
- Teléfono de contacto
- Observaciones

### Módulo 3: Productos

Permite registrar productos disponibles de AJE.

**Campos principales:**

- ID del producto
- Nombre
- Categoría
- Precio unitario
- Stock disponible
- Estado

### Módulo 4: Pedidos

Registra la solicitud general del pedido.

**Campos principales:**

- ID del pedido
- ID del cliente
- ID de tienda
- Fecha de pedido
- Fecha de entrega
- Estado
- Total
- Observaciones

### Módulo 5: Detalle de pedidos

Registra los productos incluidos dentro de cada pedido.

**Campos principales:**

- ID del detalle
- ID del pedido
- ID del producto
- Cantidad
- Precio unitario
- Subtotal

### Módulo 6: Chat de pedidos

Permite almacenar mensajes entre el cliente y el sistema.

**Campos principales:**

- ID del mensaje
- ID del pedido
- ID del cliente
- Mensaje
- Tipo de mensaje
- Fecha
- Confirmación

### Módulo 7: Notificaciones

Permite registrar las notificaciones enviadas al cliente.

**Campos principales:**

- ID de notificación
- ID del pedido
- ID del cliente
- Tipo
- Mensaje
- Estado de envío
- Fecha

---

## 16. Modelo de base de datos propuesto

### Tabla: users

| Campo | Tipo sugerido | Descripción |
|---|---|---|
| id | UUID | Identificador del usuario |
| name | TEXT | Nombre del cliente |
| email | TEXT | Correo |
| phone | TEXT | Teléfono |
| password_hash | TEXT | Contraseña cifrada |
| created_at | TIMESTAMP | Fecha de creación |

### Tabla: stores

| Campo | Tipo sugerido | Descripción |
|---|---|---|
| id | UUID | Identificador de la tienda |
| user_id | UUID | Cliente propietario |
| name | TEXT | Nombre de la tienda |
| address | TEXT | Dirección |
| latitude | DECIMAL | Latitud |
| longitude | DECIMAL | Longitud |
| phone | TEXT | Teléfono de la tienda |
| created_at | TIMESTAMP | Fecha de creación |

### Tabla: products

| Campo | Tipo sugerido | Descripción |
|---|---|---|
| id | UUID | Identificador del producto |
| name | TEXT | Nombre del producto |
| category | TEXT | Categoría |
| price | DECIMAL | Precio unitario |
| stock | INTEGER | Stock disponible |
| active | BOOLEAN | Estado del producto |
| created_at | TIMESTAMP | Fecha de creación |

### Tabla: orders

| Campo | Tipo sugerido | Descripción |
|---|---|---|
| id | UUID | Identificador del pedido |
| user_id | UUID | Cliente que realiza el pedido |
| store_id | UUID | Tienda asociada |
| status | TEXT | Estado del pedido |
| delivery_date | DATE | Fecha de entrega |
| total | DECIMAL | Total del pedido |
| notes | TEXT | Observaciones |
| created_at | TIMESTAMP | Fecha de creación |

### Tabla: order_items

| Campo | Tipo sugerido | Descripción |
|---|---|---|
| id | UUID | Identificador del detalle |
| order_id | UUID | Pedido relacionado |
| product_id | UUID | Producto solicitado |
| quantity | INTEGER | Cantidad |
| unit_price | DECIMAL | Precio unitario |
| subtotal | DECIMAL | Subtotal |

### Tabla: chat_messages

| Campo | Tipo sugerido | Descripción |
|---|---|---|
| id | UUID | Identificador del mensaje |
| user_id | UUID | Cliente |
| order_id | UUID | Pedido relacionado |
| message | TEXT | Contenido del mensaje |
| sender | TEXT | Usuario, sistema o empresa |
| created_at | TIMESTAMP | Fecha del mensaje |

### Tabla: notifications

| Campo | Tipo sugerido | Descripción |
|---|---|---|
| id | UUID | Identificador de notificación |
| user_id | UUID | Cliente |
| order_id | UUID | Pedido relacionado |
| type | TEXT | Chat o correo |
| message | TEXT | Mensaje enviado |
| status | TEXT | Enviado, pendiente o fallido |
| created_at | TIMESTAMP | Fecha de creación |

---

## 17. Endpoints propuestos

### Autenticación

- `POST /auth/register`
- `POST /auth/login`

### Clientes

- `GET /users/me`
- `PUT /users/me`

### Tiendas

- `POST /stores`
- `GET /stores`
- `GET /stores/{store_id}`
- `PUT /stores/{store_id}`
- `DELETE /stores/{store_id}`

### Productos

- `POST /products`
- `GET /products`
- `GET /products/{product_id}`
- `PUT /products/{product_id}`
- `DELETE /products/{product_id}`

### Pedidos

- `POST /orders/draft`
- `POST /orders/confirm`
- `GET /orders`
- `GET /orders/{order_id}`
- `PUT /orders/{order_id}/status`

### Procesamiento de lenguaje natural

- `POST /nlp/parse-order`

**Entrada esperada:**

```json
{
  "text": "Quiero 4 Coca-Colas y 2 paquetes de Bolt para el viernes",
  "store_id": "uuid"
}
```

**Respuesta esperada:**

```json
{
  "products": [
    {
      "name": "Coca-Cola",
      "quantity": 4,
      "unit_price": 10,
      "subtotal": 40
    },
    {
      "name": "Bolt",
      "quantity": 2,
      "unit_price": 8,
      "subtotal": 16
    }
  ],
  "delivery_date": "2026-05-22",
  "total": 56,
  "requires_confirmation": true
}
```

### Chat

- `POST /chat/message`
- `GET /chat/{order_id}`

### Notificaciones

- `POST /notifications/email`
- `POST /notifications/chat`
- `GET /notifications`

---

## 18. Pantallas necesarias

### App móvil

1. Pantalla de inicio de sesión.
2. Pantalla de registro de cliente.
3. Pantalla de registro de tienda.
4. Pantalla de ubicación de tienda.
5. Pantalla de chat de pedidos.
6. Pantalla de dictado por voz.
7. Pantalla de extracto del pedido.
8. Pantalla de confirmación.
9. Pantalla de historial de pedidos.
10. Pantalla de detalle del pedido.

### Panel web/tablet para AJE

1. Login del panel.
2. Dashboard principal.
3. Lista de pedidos pendientes.
4. Detalle del pedido.
5. Cambio de estado del pedido.
6. Gestión de productos.
7. Gestión de precios.
8. Gestión de stock.
9. Lista de clientes/tiendas.
10. Vista de notificaciones.

---

## 19. Sprints del proyecto

Cada sprint debe terminar con un producto final verificable y presentable.

| Sprint | Responsable principal | Producto final / entregable | Rol receptor |
|---|---|---|---|
| Sprint 0 | Todo el equipo | Tema, descripción, alcance, roles, criterios de aceptación y contrato | Stakeholder / Ing. Claudia Ureña Hinojosa |
| Sprint 1 | Todo el equipo | Sistema completo sin interpretación NLP ni voz: Backend, BD, App móvil (registro, tiendas, pedidos manuales, historial), Panel web AJE | Project Manager / Stakeholder |
| Sprint 2 | Luz + apoyo | Implementación del chat con procesamiento de lenguaje natural escrito y generación de extracto | Cliente final |
| Sprint 3 | Valentina + apoyo | Reconocimiento de voz en React Native, conversión a texto y envío al NLP | Cliente final / Empresa |
| Sprint 4 | Todo el equipo | Pruebas completas: unitarias, integración, usabilidad, aceptación y corrección de errores | Cliente final / Stakeholder |
| Sprint 5 | Todo el equipo | Reportes de aceptación del producto, métricas, encuestas de satisfacción y presentación final | Stakeholder |

> **Nota:** La documentación detallada de cada sprint se encuentra en la carpeta `sprints/` del repositorio.

---

## 20. Reglas de interacción

- Máximo 10 interacciones formales con la stakeholder.
- Las dudas deben agruparse por sprint.
- Cada sprint debe terminar con un entregable funcional.
- No se aceptarán cambios que afecten el alcance si reducen la posibilidad de terminar en menos de un mes.
- Las decisiones importantes deben quedar registradas.
- Las pruebas deben hacerse con casos reales simulados.

---

## 21. Reglas de eliminación de integrante

Un integrante podrá ser retirado del equipo si acumula tres llamadas de atención formales.

**Reglas:**

- Cada llamada de atención debe realizarse por carta.
- No se pueden entregar dos o tres cartas el mismo día.
- Las llamadas de atención deben estar justificadas.
- Las faltas deben estar relacionadas con incumplimiento de tareas, falta de participación o afectación directa al avance del proyecto.

---

## 22. Criterios de aceptación

El proyecto será considerado aceptado si cumple con lo siguiente:

- El usuario puede registrarse.
- El usuario puede registrar su tienda.
- El usuario puede guardar nombre, dirección y ubicación de tienda.
- El usuario puede escribir un pedido.
- El usuario puede dictar un pedido por voz.
- El sistema convierte la voz en texto.
- El backend interpreta el pedido.
- El sistema identifica productos y cantidades.
- El sistema muestra precio unitario.
- El sistema calcula subtotal por producto.
- El sistema calcula el total del pedido.
- El sistema muestra un extracto antes de enviar.
- El usuario puede confirmar el pedido.
- El pedido se guarda en estado Pendiente.
- El pedido aparece en el panel de AJE.
- AJE puede cambiar el estado del pedido.
- El cliente recibe notificación por chat.
- El cliente recibe notificación por correo.
- El sistema valida stock básico.
- El MVP puede ser presentado en una prueba real simulada.

---

## 23. Red flags del proyecto

Estas son las principales advertencias que deben evitarse:

- No prometer una inteligencia artificial perfecta.
- No depender únicamente del reconocimiento por voz.
- No hacer un ERP completo.
- No agregar pagos.
- No agregar facturación.
- No agregar rutas de distribución.
- No entrenar un modelo propio.
- No cambiar de tecnología a mitad del proyecto.
- No crear demasiados módulos.
- No diseñar pantallas innecesarias.
- No intentar integrar sistemas reales de AJE.
- No dejar el pedido sin confirmación manual.
- No guardar pedidos sin precio.
- No guardar pedidos sin stock.
- No enviar pedidos sin extracto previo.
- No dejar la ubicación como dato opcional si se requiere entrega.

---

## 24. Riesgos técnicos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Fallo en reconocimiento de voz | Alto | Permitir corrección manual |
| Error al interpretar productos | Alto | Usar catálogo cerrado de productos |
| Falta de stock | Medio | Validar antes de confirmar |
| Cambios de alcance | Alto | Respetar MVP |
| Poco tiempo de desarrollo | Alto | Priorizar flujo principal |
| Errores en precios | Alto | Guardar precio desde catálogo |
| Problemas de conexión | Medio | Validar errores y mostrar mensajes claros |
| Complejidad del panel | Medio | Hacer panel simple y funcional |

---

## 25. Instalación del proyecto

### Requisitos generales

- Node.js
- pnpm
- Python
- FastAPI
- Cuenta de Supabase
- Expo o entorno React Native
- Navegador web
- Git

---

## 26. Estructura sugerida del repositorio

```text
preventista-inteligente-aje/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── services/
│   │   ├── models/
│   │   └── utils/
│   ├── requirements.txt
│   └── README.md
│
├── mobile/
│   ├── src/
│   │   ├── screens/
│   │   ├── components/
│   │   ├── services/
│   │   └── hooks/
│   ├── package.json
│   └── README.md
│
├── panel/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   └── services/
│   ├── package.json
│   └── README.md
│
├── sprints/
│   ├── README.md
│   ├── sprint-1/
│   ├── sprint-2/
│   ├── sprint-3/
│   ├── sprint-4/
│   └── sprint-5/
│
└── README.md
```

---

## 27. Variables de entorno sugeridas

### Backend

```env
SUPABASE_URL=
SUPABASE_KEY=
DATABASE_URL=
EMAIL_HOST=
EMAIL_PORT=
EMAIL_USER=
EMAIL_PASSWORD=
```

### App móvil

```env
API_URL=
```

### Panel web

```env
VITE_API_URL=
```

---

## 28. Comandos sugeridos

### Backend

```bash
cd backend
python -m venv venv
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### App móvil

```bash
cd mobile
npm install
npm start
```

### Panel web

```bash
cd panel
npm install
npm run dev
```

---

## 29. Ejemplo de pedido

**Entrada del usuario:**

> Quiero 4 Coca-Colas y 2 paquetes de Bolt para el viernes.

**Extracto generado:**

```text
Resumen del pedido:

Tienda: Tienda San Miguel
Dirección: Av. Blanco Galindo
Fecha de entrega: Viernes

Productos:
1. Coca-Cola
   Cantidad: 4
   Precio unitario: Bs 10
   Subtotal: Bs 40

2. Bolt
   Cantidad: 2
   Precio unitario: Bs 8
   Subtotal: Bs 16

Total: Bs 56

¿Deseas confirmar este pedido?
```

**Confirmación del usuario:**

> Confirmado

**Respuesta del sistema:**

> Tu pedido fue enviado correctamente a AJE y se encuentra en estado Pendiente.
> Te notificaremos por este chat y por correo cuando la empresa lo revise.

---

## 30. Ejemplo de notificación por cambio de estado

Cuando AJE confirma el pedido:

```text
Tu pedido #0001 fue confirmado por AJE.

Resumen:
- Coca-Cola x4
- Bolt x2
- Total: Bs 56
- Fecha de entrega: Viernes
- Estado: Confirmado
```

---

## 31. Conclusión

Este proyecto busca crear un MVP funcional de preventista inteligente para automatizar la recepción de pedidos comerciales mediante lenguaje natural escrito o por voz.

La solución propuesta permite reducir errores en pedidos, mejorar la comunicación entre cliente y empresa, controlar precios y stock, registrar tiendas con ubicación y mantener informado al cliente mediante notificaciones por chat y correo.

El alcance está limitado a una solución funcional y presentable en menos de un mes, evitando módulos complejos que puedan afectar la entrega final.