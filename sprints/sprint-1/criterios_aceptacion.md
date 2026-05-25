# ✅ Sprint 1 — Criterios de Aceptación

## Autenticación

- [ ] El usuario puede registrarse con nombre, email, teléfono y contraseña.
- [ ] El usuario puede iniciar sesión y recibe un token JWT válido.
- [ ] Los endpoints protegidos rechazan solicitudes sin token válido.
- [ ] La sesión persiste en la app móvil (no pide login cada vez que se abre).

---

## Tiendas

- [ ] El usuario puede crear una tienda con nombre, dirección, teléfono y ubicación.
- [ ] La ubicación se captura desde un mapa interactivo (latitud y longitud).
- [ ] El usuario puede ver la lista de sus tiendas.
- [ ] El usuario puede editar los datos de una tienda existente.
- [ ] El usuario puede eliminar una tienda.

---

## Productos

- [ ] El catálogo de productos existe con datos semilla (mínimo 10 productos de AJE).
- [ ] Cada producto tiene nombre, categoría, precio unitario, stock y estado.
- [ ] La lista de productos es visible desde la app móvil y el panel web.
- [ ] AJE puede agregar, editar y desactivar productos desde el panel.

---

## Pedidos (creación manual)

- [ ] El cliente puede crear un pedido seleccionando productos del catálogo.
- [ ] El cliente puede indicar cantidades para cada producto.
- [ ] El sistema muestra precio unitario, subtotal por producto y total del pedido.
- [ ] El sistema valida que haya stock suficiente antes de aceptar el pedido.
- [ ] El cliente debe seleccionar una tienda y una fecha de entrega.
- [ ] El sistema genera un extracto del pedido para revisión.
- [ ] El cliente puede confirmar el pedido (pasa de borrador a pendiente).
- [ ] El pedido confirmado aparece en el panel de AJE.

---

## Panel web AJE

- [ ] AJE puede iniciar sesión en el panel web.
- [ ] El dashboard muestra un resumen de pedidos por estado.
- [ ] AJE puede ver la lista de pedidos con filtros por estado.
- [ ] AJE puede ver el detalle completo de un pedido.
- [ ] AJE puede cambiar el estado del pedido (Pendiente → Confirmado / Rechazado / En proceso).
- [ ] AJE puede ver y gestionar productos (CRUD completo).
- [ ] AJE puede ver la lista de clientes con sus tiendas.

---

## Chat y Notificaciones

- [ ] El chat muestra mensajes del sistema cuando se crea y confirma un pedido.
- [ ] Cuando AJE cambia el estado del pedido, se genera un mensaje de chat automático.
- [ ] Cuando AJE cambia el estado del pedido, se envía un correo electrónico al cliente.
- [ ] El cliente puede ver sus notificaciones en la app.

---

## Infraestructura

- [ ] El backend FastAPI está desplegado y responde correctamente.
- [ ] La base de datos Supabase tiene todas las tablas del modelo.
- [ ] La app móvil se ejecuta correctamente en un emulador o dispositivo Android.
- [ ] El panel web se ejecuta correctamente en un navegador.
- [ ] Las variables de entorno están configuradas correctamente.

---

## Criterio global de completitud

> **El Sprint 1 se considera completo cuando un cliente puede registrarse, crear una tienda con ubicación, crear un pedido manual seleccionando productos, confirmar el pedido, y AJE puede verlo y cambiar su estado desde el panel web, generando notificaciones automáticas.**
