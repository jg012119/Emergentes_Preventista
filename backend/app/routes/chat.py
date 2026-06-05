"""Chat message routes."""

import json
import re
import unicodedata
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.config import get_supabase_admin
from app.models.schemas import ChatFeedbackOut, ChatFeedbackRequest, ChatMessageCreate, ChatMessageOut
from app.routes.nlp import draft_order_chat_reply
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/chat", tags=["chat"])

CHAT_ACTION_PREFIX = "@@action "
ORDER_LIST_LIMIT = 5
AGENT_SENDERS = {"empresa", "system", "assistant", "agent"}

STATUS_LABELS = {
    "borrador": "Borrador",
    "pendiente": "Pendiente",
    "confirmado": "Confirmado",
    "rechazado": "Rechazado",
    "en_proceso": "En proceso",
    "pagado": "Pagado",
}

STATUS_PLURAL_LABELS = {
    "borrador": "borradores",
    "pendiente": "pendientes",
    "confirmado": "confirmados",
    "rechazado": "rechazados",
    "en_proceso": "en proceso",
    "pagado": "pagados",
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
    "pagado": "pagado",
    "pagados": "pagado",
}


def _action_line(payload: dict) -> str:
    return f"{CHAT_ACTION_PREFIX}{json.dumps(payload, ensure_ascii=True, separators=(',', ':'))}"


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


# Patterns like "no quiero cocas, solo agua" - extract the 'solo X' part
_NEGATION_REDIRECT_RE = re.compile(
    r"\bsolo\s+(.+?)(?:\s*(?:porfavor|por\s+favor|please|gracias|porf))?\s*$",
    re.IGNORECASE,
)
_PURE_NEGATION_NORMALIZED = {
    "no", "no gracias", "no por ahora", "no quiero nada",
    "ninguno", "nada", "no nada", "no quiero", "no necesito",
}


def _get_redirect_text(message: str | None) -> str | None:
    """If the message starts with a negation and then has 'solo X', return 'X'."""
    if not message:
        return None
    text = _normalize_text(message)
    # Pure negation without a redirect
    if text in _PURE_NEGATION_NORMALIZED:
        return None
    # Check for combined pattern: starts with negation and contains 'solo X'
    m = _NEGATION_REDIRECT_RE.search(message)
    if m and any(neg in text.split() for neg in ("no", "sin", "mejor")):
        return m.group(1).strip()
    return None


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
    return f"Pedido #{order['id'][:8]} - {store} - {status} - {_money(order.get('total'))} - entrega {delivery}"


def _order_action(db, order: dict) -> dict:
    store = _store_name(db, order.get("store_id"))
    status = _status_label(order.get("status"))
    delivery = order.get("delivery_date") or "sin fecha"
    return {
        "type": "order",
        "order_id": order["id"],
        "label": f"Ver pedido #{order['id'][:8]}",
        "store": store,
        "status": status,
        "total": _money(order.get("total")),
        "delivery": delivery,
    }


def _orders_action_label(status_filter: str | None) -> str:
    if status_filter:
        return f"Ver mas pedidos {STATUS_PLURAL_LABELS.get(status_filter, _status_label(status_filter).lower())}"
    return "Ver mas pedidos"


def _append_followup_actions(lines: list[str], status_filter: str | None = None) -> None:
    lines.append(_action_line({
        "type": "orders",
        "status": status_filter,
        "label": _orders_action_label(status_filter),
    }))
    lines.append(_action_line({
        "type": "message",
        "message": "Menu",
        "label": "Ver menu",
    }))


def _list_orders_message(db, user_id: str, status_filter: str | None = None) -> str:
    query = db.table("orders").select("*").eq("user_id", user_id).order("created_at", desc=True)
    if status_filter:
        query = query.eq("status", status_filter)
    orders = query.limit(ORDER_LIST_LIMIT + 1).execute().data
    visible_orders = orders[:ORDER_LIST_LIMIT]

    if not visible_orders:
        if status_filter:
            lines = [f"No encontre pedidos en estado {_status_label(status_filter).lower()}."]
        else:
            lines = ["Todavia no tienes pedidos registrados."]
        lines.append("Puedo mostrarte el menu para armar uno nuevo.")
        lines.append(_action_line({"type": "message", "message": "Menu", "label": "Ver menu"}))
        return "\n".join(lines)

    title = (
        f"Tus ultimos {min(len(visible_orders), ORDER_LIST_LIMIT)} pedidos en estado {_status_label(status_filter).lower()}:"
        if status_filter
        else f"Tus ultimos {min(len(visible_orders), ORDER_LIST_LIMIT)} pedidos:"
    )
    lines = [title]
    lines.extend(f"- {_order_line(db, order)}" for order in visible_orders)
    lines.append("Toca un pedido para ver el detalle completo.")
    if len(orders) > ORDER_LIST_LIMIT:
        lines.append("Hay mas resultados disponibles con este mismo filtro.")
    for order in visible_orders:
        lines.append(_action_line(_order_action(db, order)))
    _append_followup_actions(lines, status_filter)
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
    lines = [
        f"El pedido #{order['id'][:8]} esta en estado {_status_label(order.get('status')).lower()}.\n"
        f"Sucursal: {_store_name(db, order.get('store_id'))}\n"
        f"Entrega: {order.get('delivery_date') or 'sin fecha'}\n"
        f"Productos: {item_count}\n"
        f"Total: {_money(order.get('total'))}"
    ]
    lines.append(_action_line(_order_action(db, order)))
    lines.append(_action_line({"type": "message", "message": "Menu", "label": "Ver menu"}))
    return "\n".join(lines)


def _build_chat_reply(db, user_id: str, body: ChatMessageCreate) -> str | None:
    if _is_structured_order_message(body.message):
        return None

    text = _normalize_text(body.message)
    status_filter = _find_status_filter(text)

    # Words that confirm the order or signal finishing
    _CONFIRMATION_WORDS = {
        "si", "sí", "ok", "okay", "dale", "confirmar", "pagar", "acabar", "listo", "terminar", "finalizar", "confirmo",
    }
    if text in _PURE_NEGATION_NORMALIZED:
        return "Entendido, sin problema. Avisame cuando necesites algo."
    # Confirmation words (e.g., pagar, acabar) should finalize the order
    if any(word in text.split() for word in _CONFIRMATION_WORDS):
        # Try to fetch the active order details
        active_order_id = body.order_id or (body.context or {}).get("active_order_id")
        if active_order_id:
            # Retrieve the order
            order_res = db.table("orders").select("*").eq("id", active_order_id).eq("user_id", user_id).execute()
            if order_res.data:
                order = order_res.data[0]
                # Retrieve order items
                items = db.table("order_items").select("*").eq("order_id", order["id"]).execute().data or []
                if items:
                    lines = ["Pedido finalizado con los siguientes productos:"]
                    for item in items:
                        qty = item.get("quantity") or 1
                        # Get product name if available
                        product_name = item.get("product_name")
                        if not product_name:
                            # fallback to product id lookup
                            prod = db.table("products").select("name").eq("id", item.get("product_id")).execute().data
                            product_name = prod[0]["name"] if prod else str(item.get("product_id"))
                        lines.append(f"- {qty} x {product_name}")
                    return "\n".join(lines)
        # Default fallback when no active order or no items
        return "Pedido finalizado. Gracias por tu compra."

    if "menu" in text or "catalogo" in text or "productos" in text:
        return _build_product_menu(db, user_id)

    if "estado" in text or "seguimiento" in text or "como va" in text:
        return _order_status_message(db, user_id, body.order_id)

    if "lista" in text or "ordenes" in text:
        return _list_orders_message(db, user_id, status_filter)

    if status_filter:
        return _list_orders_message(db, user_id, status_filter)

    # Handle "no quiero X, solo Y" → redirect to "Y" as the new request
    redirect_text = _get_redirect_text(body.message)
    if redirect_text:
        # Build NLP reply with just the redirected product text
        active_order_id = body.order_id or (body.context or {}).get("active_order_id")
        nlp_reply = draft_order_chat_reply(
            db,
            text=redirect_text,
            user_id=user_id,
            requested_store_id=None,
            active_order_id=active_order_id,
            context=body.context,
        )
        if nlp_reply:
            return nlp_reply

    active_order_id = body.order_id or (body.context or {}).get("active_order_id")
    # In caso de que el usuario aún no haya especificado un pedido, sigue el flujo normal
    nlp_reply = draft_order_chat_reply(
        db,
        text=body.message,
        user_id=user_id,
        requested_store_id=None,
        active_order_id=active_order_id,
        context=body.context,
    )
    if nlp_reply:
        return nlp_reply

    if "pedido" in text or "pedidos" in text:
        return _list_orders_message(db, user_id, status_filter)

    return (
        "Puedo ayudarte con: menu de productos, estado del pedido, lista de pedidos, "
        "pedidos pendientes, confirmados, rechazados, en proceso o pagados."
    )


def _attach_feedback(db, user_id: str, messages: list[dict]) -> list[dict]:
    message_ids = {message.get("id") for message in messages if message.get("id")}
    if not message_ids:
        return messages

    try:
        feedback_rows = db.table("agent_feedback").select("message_id, rating").eq("user_id", user_id).execute().data or []
    except Exception:
        feedback_rows = []

    ratings = {
        row.get("message_id"): row.get("rating")
        for row in feedback_rows
        if row.get("message_id") in message_ids
    }
    return [
        {**message, "feedback_rating": ratings.get(message.get("id"))}
        for message in messages
    ]


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
    return [ChatMessageOut(**m) for m in _attach_feedback(db, user_id, general_messages[-100:])]


@router.post("/messages/{message_id}/feedback", response_model=ChatFeedbackOut, status_code=201)
async def rate_agent_message(
    message_id: str,
    body: ChatFeedbackRequest,
    user_id: str = Depends(get_current_user_id),
):
    db = get_supabase_admin()
    message = (
        db.table("chat_messages")
        .select("*")
        .eq("id", message_id)
        .eq("user_id", user_id)
        .execute()
        .data
    )
    if not message:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")

    message_row = message[0]
    if str(message_row.get("sender") or "").lower() not in AGENT_SENDERS:
        raise HTTPException(status_code=400, detail="Solo se puede calificar respuestas del agente")

    payload = {
        "user_id": user_id,
        "message_id": message_id,
        "order_id": message_row.get("order_id"),
        "rating": body.rating,
        "comment": body.comment,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "context": {
            **(body.context or {}),
            "message": message_row.get("message"),
            "sender": message_row.get("sender"),
        },
    }

    existing = (
        db.table("agent_feedback")
        .select("id")
        .eq("user_id", user_id)
        .eq("message_id", message_id)
        .execute()
        .data
    )
    if existing:
        result = (
            db.table("agent_feedback")
            .update(payload)
            .eq("id", existing[0]["id"])
            .execute()
        )
    else:
        result = db.table("agent_feedback").insert(payload).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="No se pudo guardar el feedback")
    return ChatFeedbackOut(**result.data[0])


@router.get("/{order_id}", response_model=list[ChatMessageOut])
async def get_chat(order_id: str, user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    result = (
        db.table("chat_messages")
        .select("*")
        .eq("order_id", order_id)
        .order("created_at")
        .execute()
    )
    return [ChatMessageOut(**m) for m in _attach_feedback(db, user_id, result.data)]


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
    return [ChatMessageOut(**m) for m in _attach_feedback(db, user_id, result.data)]
