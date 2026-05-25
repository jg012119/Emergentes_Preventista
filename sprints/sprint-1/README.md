# 🏗️ Sprint 1 — Sistema Base Completo

## Objetivo

Construir la infraestructura completa del proyecto: backend, base de datos, aplicación móvil y panel web con **todas las funcionalidades operativas**, pero **sin procesamiento de lenguaje natural ni reconocimiento de voz**.

Los pedidos en este sprint se crean de forma **manual** (selección de productos desde catálogo), sentando las bases para que en sprints posteriores se agregue la interpretación por texto y voz.

---

## Alcance del sprint

### ✅ Incluido

- **Backend FastAPI completo** con todos los endpoints CRUD.
- **Base de datos Supabase** con todas las tablas del modelo.
- **App móvil React Native** con registro, login, tiendas, pedidos manuales e historial.
- **Panel web React + Vite** para AJE con gestión de pedidos, productos, stock y clientes.
- **Sistema de notificaciones** básico (chat interno + correo).
- **Control de stock y precios** desde el backend.

### ❌ Excluido (se hará en sprints posteriores)

- Procesamiento de lenguaje natural (NLP) para interpretar pedidos por texto.
- Reconocimiento de voz.
- Generación automática de extracto desde texto libre.

---

## Responsables

| Componente | Responsable | Apoyo |
|---|---|---|
| Backend FastAPI | Jairo Guzman | Luz, Valentina |
| Base de datos Supabase | Jairo Guzman | Todo el equipo |
| App móvil React Native | Luz Laredo | Valentina |
| Panel web React + Vite | Valentina Trigo | Luz |
| Notificaciones | Todo el equipo | — |

---

## Duración estimada

**1 semana**

---

## Dependencias

- Cuenta de Supabase activa.
- Entorno Node.js y Python configurado.
- Repositorio Git inicializado.

---

## Notas técnicas

- Los pedidos se crean **seleccionando productos del catálogo**, no escribiendo texto libre.
- La pantalla de chat existe pero funciona como un **log de mensajes del sistema**, no como entrada NLP.
- El extracto del pedido se genera a partir de los **items seleccionados manualmente**.
- El panel web consume la misma API FastAPI que la app móvil.
