"""Chat message routes."""

import unicodedata

from fastapi import APIRouter, Depends, HTTPException

from app.config import get_supabase_admin
from app.models.schemas import ChatMessageCreate, ChatMessageOut
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/chat", tags=["chat"])

STATUS_LABELS = {
    "borrador": "Borrador",
    "pendiente": "Pendiente",
    "confirmado": "Confirmado",
    "rechazado": "Rechazado",
    "en_proceso": "En proceso",
}

STATUS_ALIASES = {
    "borrador": "borrador",
    "borradores": "borrador",
    "pendiente": "pendiente",
    "pendientes": "pendiente",
    "confirmado": "confirmado",
    "confirmados": "confirmado",
    "rechazado": "rechazado",
    "rechazados": "rechazado",
    "proceso": "en_proceso",
    "procesando": "en_proceso",
    "en proceso": "en_proceso",
    "en_proceso": "en_proceso",
}


def _first_name(name: str | None) -> str:
    clean = (name or "cliente").strip()
    return clean.split()[0] if clean else "cliente"


def _build_product_menu(db, user_id: str) -> str:
    user = db.table("users").select("name").eq("id", user_id).execute().data
    name = _first_name(user[0].get("name") if user else None)
    products = (
        db.table("products")
        .select("*")
        .eq("active", True)
        .order("category")
        .order("name")
        .execute()
        .data
    )

    if not products:
        return f"Hola {name}, soy tu preventista AJE. Por ahora no tengo productos activos para mostrarte."

    lines = [f"Hola {name}, soy tu preventista AJE. Te paso el menu de productos disponibles:"]
    current_category = None
    for product in products:
        category = product.get("category") or "Productos"
        if category != current_category:
            current_category = category
            lines.append(f"\n{category}")
        lines.append(f"- {product.get('name', 'Producto')} - Bs {float(product.get('price') or 0):.2f}")
    lines.append("\nPuedes responder con cantidad y producto, por ejemplo: dos Big Cola 3L.")
    return "\n".join(lines)


def _normalize_text(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.lower().replace("_", " ").split())


def _is_structured_order_message(message: str | None) -> bool:
    text = _normalize_text(message)
    return text.startswith("pedido estructurado desde catalogo:")


def _money(value) -> str:
    try:
        return f"Bs {float(value or 0):.2f}"
    except (TypeError, ValueError):
        return "Bs 0.00"


def _status_label(status: str | None) -> str:
    return STATUS_LABELS.get(status or "", status or "Sin estado")


def _find_status_filter(text: str) -> str | None:
    for alias, status in STATUS_ALIASES.items():
        if alias in text:
            return status
    return None


def _store_name(db, store_id: str | None) -> str:
    if not store_id:
        return "Sin sucursal"
    store = db.table("stores").select("name").eq("id", store_id).execute()
    return store.data[0]["name"] if store.data else "Sin sucursal"


def _order_line(db, order: dict) -> str:
    store = _store_name(db, order.get("store_id"))
    status = _status_label(order.get("status"))
    delivery = order.get("delivery_date") or "sin fecha"
    return f"#{order['id'][:8]} - {store} - {status} - {_money(order.get('total'))} - entrega {delivery}"


def _list_orders_message(db, user_id: str, status_filter: str | None = None) -> str:
    query = db.table("orders").select("*").eq("user_id", user_id).order("created_at", desc=True)
    if status_filter:
        query = query.eq("status", status_filter)
    orders = query.limit(5).execute().data

    if not orders:
        if status_filter:
            return f"No encontre pedidos en estado {_status_label(status_filter).lower()}."
        return "Todavia no tienes pedidos registrados."

    title = (
        f"Tus ultimos pedidos en estado {_status_label(status_filter).lower()}:"
        if status_filter
        else "Tus ultimos pedidos:"
    )
    lines = [title]
    lines.extend(f"- {_order_line(db, order)}" for order in orders)
    return "\n".join(lines)


def _order_status_message(db, user_id: str, order_id: str | None) -> str:
    query = db.table("orders").select("*").eq("user_id", user_id)
    if order_id:
        query = query.eq("id", order_id)
    else:
        query = query.order("created_at", desc=True).limit(1)

    orders = query.execute().data
    if not orders:
        return "No encontre un pedido para consultar. Puedes pedirme: lista de pedidos."

    order = orders[0]
    items = db.table("order_items").select("*").eq("order_id", order["id"]).execute().data
    item_count = sum(int(item.get("quantity") or 0) for item in items)
    return (
        f"El pedido #{order['id'][:8]} esta en estado {_status_label(order.get('status')).lower()}.\n"
        f"Sucursal: {_store_name(db, order.get('store_id'))}\n"
        f"Entrega: {order.get('delivery_date') or 'sin fecha'}\n"
        f"Productos: {item_count}\n"
        f"Total: {_money(order.get('total'))}"
    )


def _build_chat_reply(db, user_id: str, body: ChatMessageCreate) -> str | None:
    if _is_structured_order_message(body.message):
        return None

    text = _normalize_text(body.message)
    status_filter = _find_status_filter(text)

    if "menu" in text or "catalogo" in text or "productos" in text:
        return _build_product_menu(db, user_id)

    if "estado" in text or "seguimiento" in text or "como va" in text:
        return _order_status_message(db, user_id, body.order_id)

    if "pedido" in text or "pedidos" in text or "ordenes" in text or "lista" in text:
        return _list_orders_message(db, user_id, status_filter)

    if status_filter:
        return _list_orders_message(db, user_id, status_filter)

    return (
        "Puedo ayudarte con: menu de productos, estado del pedido, lista de pedidos, "
        "pedidos pendientes, confirmados, rechazados o en proceso."
    )


@router.post("/message", response_model=ChatMessageOut, status_code=201)
async def send_message(body: ChatMessageCreate, user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    result = db.table("chat_messages").insert({
        "user_id": user_id,
        "order_id": body.order_id,
        "message": body.message,
        "sender": body.sender,
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Error al enviar mensaje")

    reply = _build_chat_reply(db, user_id, body) if body.sender == "user" else None
    if reply:
        db.table("chat_messages").insert({
            "user_id": user_id,
            "order_id": body.order_id,
            "message": reply,
            "sender": "empresa",
        }).execute()

    return ChatMessageOut(**result.data[0])


@router.get("/general/messages", response_model=list[ChatMessageOut])
async def get_general_chat(user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    result = (
        db.table("chat_messages")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at")
        .execute()
    )
    general_messages = [m for m in result.data if m.get("order_id") is None]
    return [ChatMessageOut(**m) for m in general_messages[-100:]]


@router.get("/{order_id}", response_model=list[ChatMessageOut])
async def get_chat(order_id: str, _user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    result = (
        db.table("chat_messages")
        .select("*")
        .eq("order_id", order_id)
        .order("created_at")
        .execute()
    )
    return [ChatMessageOut(**m) for m in result.data]


@router.get("/user/all", response_model=list[ChatMessageOut])
async def get_user_chats(user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    result = (
        db.table("chat_messages")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(100)
        .execute()
    )
    return [ChatMessageOut(**m) for m in result.data]
