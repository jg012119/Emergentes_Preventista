# 📝 Sprint 1 — Backlog de Tareas

## Épica 1: Configuración del proyecto

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S1-001 | Crear repositorio Git con estructura de carpetas (`backend/`, `mobile/`, `panel/`) | Alta | 1h |
| S1-002 | Configurar proyecto FastAPI en `backend/` con estructura de rutas y servicios | Alta | 2h |
| S1-003 | Crear proyecto React Native (Expo) en `mobile/` | Alta | 1h |
| S1-004 | Crear proyecto React + Vite en `panel/` | Alta | 1h |
| S1-005 | Crear cuenta Supabase y obtener credenciales (`SUPABASE_URL`, `SUPABASE_KEY`) | Alta | 1h |
| S1-006 | Configurar variables de entorno en todos los componentes | Alta | 1h |

---

## Épica 2: Base de datos

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S1-007 | Crear tabla `users` (id, name, email, phone, password_hash, created_at) | Alta | 30min |
| S1-008 | Crear tabla `stores` (id, user_id, name, address, latitude, longitude, phone, created_at) | Alta | 30min |
| S1-009 | Crear tabla `products` (id, name, category, price, stock, active, created_at) | Alta | 30min |
| S1-010 | Crear tabla `orders` (id, user_id, store_id, status, delivery_date, total, notes, created_at) | Alta | 30min |
| S1-011 | Crear tabla `order_items` (id, order_id, product_id, quantity, unit_price, subtotal) | Alta | 30min |
| S1-012 | Crear tabla `chat_messages` (id, user_id, order_id, message, sender, created_at) | Alta | 30min |
| S1-013 | Crear tabla `notifications` (id, user_id, order_id, type, message, status, created_at) | Alta | 30min |
| S1-014 | Configurar RLS (Row Level Security) en Supabase para cada tabla | Media | 2h |
| S1-015 | Insertar datos semilla: productos iniciales de AJE (catálogo base) | Alta | 1h |

---

## Épica 3: Backend FastAPI — Autenticación

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S1-016 | `POST /auth/register` — Registro de usuario con hash de contraseña | Alta | 2h |
| S1-017 | `POST /auth/login` — Login con generación de token JWT | Alta | 2h |
| S1-018 | Middleware de autenticación JWT para proteger endpoints | Alta | 2h |

---

## Épica 4: Backend FastAPI — CRUD Usuarios

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S1-019 | `GET /users/me` — Obtener datos del usuario autenticado | Alta | 1h |
| S1-020 | `PUT /users/me` — Actualizar datos del usuario | Media | 1h |

---

## Épica 5: Backend FastAPI — CRUD Tiendas

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S1-021 | `POST /stores` — Crear tienda asociada al usuario | Alta | 1h |
| S1-022 | `GET /stores` — Listar tiendas del usuario | Alta | 1h |
| S1-023 | `GET /stores/{store_id}` — Detalle de tienda | Media | 30min |
| S1-024 | `PUT /stores/{store_id}` — Actualizar tienda | Media | 1h |
| S1-025 | `DELETE /stores/{store_id}` — Eliminar tienda | Baja | 30min |

---

## Épica 6: Backend FastAPI — CRUD Productos

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S1-026 | `POST /products` — Crear producto (solo admin/AJE) | Alta | 1h |
| S1-027 | `GET /products` — Listar productos con stock y precio | Alta | 1h |
| S1-028 | `GET /products/{product_id}` — Detalle de producto | Media | 30min |
| S1-029 | `PUT /products/{product_id}` — Actualizar producto/stock/precio | Alta | 1h |
| S1-030 | `DELETE /products/{product_id}` — Desactivar producto | Baja | 30min |

---

## Épica 7: Backend FastAPI — Pedidos (manual)

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S1-031 | `POST /orders/draft` — Crear pedido borrador con items seleccionados | Alta | 3h |
| S1-032 | `POST /orders/confirm` — Confirmar pedido (cambiar estado de borrador a pendiente) | Alta | 2h |
| S1-033 | `GET /orders` — Listar pedidos del usuario (cliente) o todos (AJE) | Alta | 2h |
| S1-034 | `GET /orders/{order_id}` — Detalle completo del pedido con items | Alta | 1h |
| S1-035 | `PUT /orders/{order_id}/status` — Cambiar estado del pedido (solo AJE) | Alta | 2h |
| S1-036 | Validación de stock al crear pedido: rechazar si no hay stock suficiente | Alta | 2h |
| S1-037 | Cálculo automático de subtotales y total del pedido | Alta | 1h |

---

## Épica 8: Backend FastAPI — Chat y Notificaciones

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S1-038 | `POST /chat/message` — Guardar mensaje en chat del pedido | Alta | 1h |
| S1-039 | `GET /chat/{order_id}` — Obtener historial de chat del pedido | Alta | 1h |
| S1-040 | `POST /notifications/chat` — Crear notificación de chat al cambiar estado | Alta | 2h |
| S1-041 | `POST /notifications/email` — Enviar correo electrónico al cambiar estado | Media | 3h |
| S1-042 | `GET /notifications` — Listar notificaciones del usuario | Media | 1h |

---

## Épica 9: App Móvil — Autenticación

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S1-043 | Como cliente, quiero registrarme con nombre, email, teléfono y contraseña | Alta | 3h |
| S1-044 | Como cliente, quiero iniciar sesión con mi email y contraseña | Alta | 2h |
| S1-045 | Persistir token JWT en AsyncStorage y manejar sesión | Alta | 2h |
| S1-046 | Pantalla de perfil del usuario | Media | 2h |

---

## Épica 10: App Móvil — Tiendas

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S1-047 | Como cliente, quiero registrar mi tienda con nombre, dirección y teléfono | Alta | 3h |
| S1-048 | Como cliente, quiero marcar la ubicación de mi tienda en un mapa | Alta | 4h |
| S1-049 | Como cliente, quiero ver la lista de mis tiendas registradas | Alta | 2h |
| S1-050 | Como cliente, quiero editar los datos de mi tienda | Media | 2h |
| S1-051 | Como cliente, quiero eliminar una tienda | Baja | 1h |

---

## Épica 11: App Móvil — Pedidos manuales

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S1-052 | Como cliente, quiero ver el catálogo de productos disponibles con precio y stock | Alta | 3h |
| S1-053 | Como cliente, quiero seleccionar productos y cantidades para crear un pedido | Alta | 4h |
| S1-054 | Como cliente, quiero ver el extracto de mi pedido antes de confirmarlo | Alta | 3h |
| S1-055 | Como cliente, quiero confirmar mi pedido para enviarlo a AJE | Alta | 2h |
| S1-056 | Como cliente, quiero seleccionar la tienda y fecha de entrega para mi pedido | Alta | 2h |
| S1-057 | Como cliente, quiero ver mi historial de pedidos con su estado actual | Alta | 3h |
| S1-058 | Como cliente, quiero ver el detalle completo de un pedido específico | Alta | 2h |

---

## Épica 12: App Móvil — Chat y Notificaciones

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S1-059 | Como cliente, quiero ver los mensajes del sistema sobre mi pedido en el chat | Alta | 3h |
| S1-060 | Como cliente, quiero recibir notificaciones cuando el estado de mi pedido cambie | Alta | 2h |
| S1-061 | Como cliente, quiero recibir un correo cuando AJE confirme o rechace mi pedido | Media | 2h |

---

## Épica 13: Panel Web AJE — Estructura base

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S1-062 | Crear login básico para el panel web de AJE | Alta | 2h |
| S1-063 | Crear dashboard principal con resumen de pedidos | Alta | 3h |
| S1-064 | Crear navegación/sidebar con secciones: Pedidos, Productos, Stock, Clientes | Alta | 2h |

---

## Épica 14: Panel Web AJE — Gestión de pedidos

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S1-065 | Como AJE, quiero ver la lista de pedidos recibidos con filtros por estado | Alta | 3h |
| S1-066 | Como AJE, quiero ver el detalle completo de un pedido (productos, cantidades, precios, totales) | Alta | 3h |
| S1-067 | Como AJE, quiero cambiar el estado del pedido (Pendiente → Confirmado / Rechazado / En proceso) | Alta | 3h |
| S1-068 | Como AJE, quiero que al cambiar el estado se notifique automáticamente al cliente | Alta | 2h |

---

## Épica 15: Panel Web AJE — Gestión de productos y stock

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S1-069 | Como AJE, quiero ver la lista de productos con nombre, categoría, precio y stock | Alta | 2h |
| S1-070 | Como AJE, quiero agregar nuevos productos al catálogo | Alta | 2h |
| S1-071 | Como AJE, quiero editar precio y stock de productos existentes | Alta | 2h |
| S1-072 | Como AJE, quiero activar o desactivar productos | Media | 1h |

---

## Épica 16: Panel Web AJE — Gestión de clientes

| ID | User Story / Tarea | Prioridad | Estimación |
|---|---|---|---|
| S1-073 | Como AJE, quiero ver la lista de clientes registrados con sus tiendas | Alta | 2h |
| S1-074 | Como AJE, quiero ver el detalle de un cliente y sus pedidos | Media | 2h |

---

## Resumen de estimaciones

| Épica | Tareas | Horas estimadas |
|---|---|---|
| Configuración del proyecto | 6 | 7h |
| Base de datos | 9 | 7h |
| Backend — Auth | 3 | 6h |
| Backend — Usuarios | 2 | 2h |
| Backend — Tiendas | 5 | 4h |
| Backend — Productos | 5 | 4h |
| Backend — Pedidos | 7 | 13h |
| Backend — Chat y Notificaciones | 5 | 8h |
| App Móvil — Auth | 4 | 9h |
| App Móvil — Tiendas | 5 | 12h |
| App Móvil — Pedidos | 7 | 19h |
| App Móvil — Chat | 3 | 7h |
| Panel Web — Estructura | 3 | 7h |
| Panel Web — Pedidos | 4 | 11h |
| Panel Web — Productos | 4 | 7h |
| Panel Web — Clientes | 2 | 4h |
| **TOTAL** | **74** | **~127h** |
