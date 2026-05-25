# 📦 Sprint 1 — Entregables

## Entregable principal

**Sistema base completo y funcional** con todas las operaciones CRUD, sin procesamiento de lenguaje natural ni reconocimiento de voz.

---

## Lista de entregables

### 1. Backend FastAPI funcional

- Proyecto FastAPI estructurado en `backend/`.
- Conexión activa con Supabase.
- Todos los endpoints implementados y probados:
  - Autenticación (registro, login, JWT).
  - CRUD de usuarios.
  - CRUD de tiendas.
  - CRUD de productos.
  - Creación y confirmación de pedidos.
  - Chat de mensajes.
  - Notificaciones (chat + correo).
- Validación de stock al crear pedidos.
- Cálculo automático de subtotales y totales.

### 2. Base de datos Supabase

- 7 tablas creadas y configuradas:
  - `users`
  - `stores`
  - `products`
  - `orders`
  - `order_items`
  - `chat_messages`
  - `notifications`
- Datos semilla de productos AJE insertados (mínimo 10 productos).
- RLS configurado para cada tabla.

### 3. App móvil React Native

- Proyecto Expo funcional en `mobile/`.
- Pantallas implementadas:
  - Inicio de sesión.
  - Registro de cliente.
  - Registro de tienda con mapa.
  - Lista de tiendas.
  - Catálogo de productos.
  - Creación de pedido manual (selección de productos).
  - Extracto del pedido.
  - Confirmación del pedido.
  - Historial de pedidos.
  - Detalle del pedido.
  - Chat del pedido (mensajes del sistema).
  - Notificaciones.
- Navegación entre pantallas funcional.
- Persistencia de sesión con JWT.

### 4. Panel web React + Vite

- Proyecto Vite funcional en `panel/`.
- Pantallas implementadas:
  - Login del panel.
  - Dashboard principal con resumen.
  - Lista de pedidos con filtros.
  - Detalle del pedido.
  - Cambio de estado del pedido.
  - Gestión de productos (CRUD).
  - Gestión de stock.
  - Lista de clientes y tiendas.
- Navegación funcional.
- Diseño responsivo para tablet.

### 5. Sistema de notificaciones

- Notificación por chat al cambiar estado del pedido.
- Notificación por correo electrónico al cambiar estado del pedido.
- Historial de notificaciones visible para el cliente.

---

## Evidencias requeridas

| Evidencia | Descripción |
|---|---|
| Captura de pantalla | Registro de usuario exitoso |
| Captura de pantalla | Registro de tienda con mapa |
| Captura de pantalla | Catálogo de productos en la app |
| Captura de pantalla | Extracto del pedido antes de confirmar |
| Captura de pantalla | Pedido confirmado en el historial |
| Captura de pantalla | Panel AJE con lista de pedidos |
| Captura de pantalla | Detalle del pedido en panel AJE |
| Captura de pantalla | Cambio de estado del pedido |
| Captura de pantalla | Notificación en chat del cliente |
| Captura de correo | Correo recibido por cambio de estado |

---

## Definición de "Done"

- [x] Código subido al repositorio Git.
- [x] Backend desplegado y funcional.
- [x] Base de datos con datos semilla.
- [x] App móvil ejecutable en emulador/dispositivo.
- [x] Panel web ejecutable en navegador.
- [x] Flujo completo de pedido manual verificado end-to-end.
- [x] Notificaciones funcionando.
- [x] Evidencias recopiladas.
