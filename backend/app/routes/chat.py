"""Chat message routes."""

import json
import re
import datetime
import unicodedata

from fastapi import APIRouter, Depends, HTTPException

from app.config import get_supabase_admin
from app.models.schemas import ChatMessageCreate, ChatMessageOut
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/chat", tags=["chat"])

CHAT_ACTION_PREFIX = "@@action "
ORDER_LIST_LIMIT = 5

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
    """Generate a chat reply based on user message.
    Handles product queries, missing presentation, quantity, stock checks,
    date prompts, order status, and menu requests.
    Supports multiple items in a single message separated by 'y', ',', '+', etc.
    """
    if _is_structured_order_message(body.message):
        return None

    text = _normalize_text(body.message)
    status_filter = _find_status_filter(text)

    # ── Generic intents (check FIRST, before product matching) ──
    if "menu" in text or "catalogo" in text or "productos" in text:
        return _build_product_menu(db, user_id)

    if "estado" in text or "seguimiento" in text or "como va" in text:
        return _order_status_message(db, user_id, body.order_id)

    if ("pedido" in text or "pedidos" in text or "ordenes" in text or "lista" in text) and not re.search(r"\d", text):
        return _list_orders_message(db, user_id, status_filter)

    if status_filter and not re.search(r"\d", text):
        return _list_orders_message(db, user_id, status_filter)

    # Import NLP helpers
    from app.routes.nlp import _best_product, _parse_quantity, _normalize, SPLIT_RE, _extract_delivery_date

    # ── Helper: extract delivery date with multiple fallbacks ──
    def _get_delivery(raw_text: str) -> str | None:
        delivery = _extract_delivery_date(raw_text)
        if delivery:
            return delivery
        # Fallback: "para <date text>"
        m = re.search(r"para\s+(.+)", raw_text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            # Remove trailing product-like words that might have been captured
            candidate = re.sub(r"\s+(y|mas|tambien)\s+.*$", "", candidate, flags=re.IGNORECASE).strip()
            if candidate:
                return candidate
        # Fallback: bare "3 de junio" pattern
        m2 = re.search(r"\b(\d{1,2}\s*de\s+\w+)\b", raw_text, re.IGNORECASE)
        if m2:
            return m2.group(1).strip()
        return None

    # ── Helper: detect size token WITHOUT matching bare numbers ──
    SIZE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(ml|l|litros?)\b", re.IGNORECASE)

    def _detect_size(seg: str) -> str | None:
        m = SIZE_RE.search(seg)
        return m.group(0).lower().strip() if m else None

    # ── Helper: detect explicit quantity (only bare numbers NOT attached to a unit) ──
    def _has_explicit_qty(seg: str) -> bool:
        """Return True if there is a number that is NOT part of a size token."""
        cleaned = SIZE_RE.sub("", seg)  # remove size tokens like '1l', '500ml'
        cleaned = re.sub(r"\b\d{1,2}\s*de\s+\w+", "", cleaned, flags=re.IGNORECASE)  # remove date patterns
        return bool(re.search(r"\b\d+\b", cleaned))

    # ── Conversation state: check previous bot message ──
    try:
        prev_msgs = (
            db.table("chat_messages")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(2)
            .execute()
            .data
        )
        if len(prev_msgs) >= 2 and prev_msgs[1].get("sender") == "empresa":
            last_bot = prev_msgs[1].get("message", "")
            last_bot_lower = last_bot.lower()

            # STATE: Awaiting presentation selection (user should answer with a number)
            if "presentación" in last_bot_lower:
                m = re.search(r"¿Qué presentación de (.+?) desea\?", last_bot)
                if m:
                    base_name = m.group(1).strip()
                    variants = (
                        db.table("products").select("*")
                        .eq("active", True).ilike("name", f"{base_name}%")
                        .execute().data
                    )
                    variants = sorted(variants, key=lambda p: p.get("name", ""))
                    try:
                        idx = int(body.message.strip()) - 1
                        if 0 <= idx < len(variants):
                            sel = variants[idx]
                            return f"¿Cuántas unidades desea de {sel.get('name')}?"
                    except ValueError:
                        pass

            # STATE: Awaiting quantity
            elif "cuántas unidades desea de" in last_bot_lower:
                try:
                    qty = int(body.message.strip())
                    m_qty = re.search(r"¿Cuántas unidades desea de (.+?)\?", last_bot)
                    if m_qty:
                        product_name = m_qty.group(1).strip()
                        prod = (
                            db.table("products").select("*")
                            .eq("active", True).eq("name", product_name)
                            .single().execute().data
                        )
                        if prod:
                            stock = prod.get("stock", 0)
                            if qty > stock:
                                return f"Lo siento, solo hay {stock} unidades de {product_name} disponibles. ¿Desea esa cantidad?"
                            delivery = _get_delivery(body.message)
                            if delivery:
                                return f"Orden recibida: {qty} unidades de {product_name} para {delivery}."
                            return f"Entendido. ¿Para qué fecha desea la entrega de {qty} unidades de {product_name}?"
                    return "Por favor, confirma el producto y la cantidad."
                except ValueError:
                    return "Por favor, ingresa una cantidad numérica válida."

            # STATE: Awaiting delivery date
            elif "fecha desea la entrega" in last_bot_lower:
                m_date = re.search(r"(\d+) unidades de (.+?)\?", last_bot)
                if m_date:
                    qty = int(m_date.group(1))
                    product_name = m_date.group(2).strip()
                    delivery = _get_delivery(body.message)
                    if delivery:
                        return f"Orden recibida: {qty} unidades de {product_name} para {delivery}."
                return "Por favor, indica la fecha de entrega (ej: mañana, 5 de junio)."
    except Exception:
        pass

    # ── Product parsing: split into segments and match each ──
    segments = [part for part in SPLIT_RE.split(_normalize(body.message)) if part]
    if not segments and body.message:
        segments = [_normalize(body.message)]

    # Global delivery date from the full message
    global_delivery = _get_delivery(body.message)

    all_products = db.table("products").select("*").eq("active", True).execute().data or []
    order_items = []

    for seg in segments:
        # Find product
        product, _score = _best_product(seg, all_products)
        if not product:
            # Singular fallback: remove trailing 's'
            singular_seg = re.sub(r"\b(\w+)s\b", r"\1", seg, flags=re.IGNORECASE)
            product, _score = _best_product(singular_seg, all_products)
        if not product:
            continue  # skip unrecognized segments

        # Size token
        size_token = _detect_size(seg)

        # If size found but doesn't match current product, find the right variant
        if size_token and size_token not in product.get("name", "").lower():
            base_name = re.sub(r"\s*\d+(?:\.\d+)?\s*(ml|l|litros?)$", "", product.get("name", ""), flags=re.IGNORECASE).strip()
            variants = [p for p in all_products if _normalize_text(p.get("name", "")).startswith(_normalize_text(base_name))]
            for v in variants:
                if size_token in v.get("name", "").lower():
                    product = v
                    break

        # Quantity
        qty = _parse_quantity(seg)
        explicit_qty = _has_explicit_qty(seg)

        # Per-segment delivery
        seg_delivery = _get_delivery(seg) or global_delivery

        order_items.append({
            "product": product,
            "size_token": size_token,
            "qty": qty,
            "explicit_qty": explicit_qty,
            "delivery": seg_delivery,
        })

    # ── No items matched ──
    if not order_items:
        return (
            "Puedo ayudarte con: menu de productos, estado del pedido, lista de pedidos, "
            "pedidos pendientes, confirmados, rechazados, en proceso o pagados."
        )

    # ── Process items: ask for missing info on the FIRST incomplete item ──
    for itm in order_items:
        product = itm["product"]
        size_token = itm["size_token"]
        qty = itm["qty"]
        explicit_qty = itm["explicit_qty"]

        # Missing presentation?
        if not size_token:
            base_name = re.sub(r"\s*\d+(?:\.\d+)?\s*(ml|l|litros?)$", "", product.get("name", ""), flags=re.IGNORECASE).strip()
            variants = [p for p in all_products if _normalize_text(p.get("name", "")).startswith(_normalize_text(base_name))]
            variants = sorted(variants, key=lambda p: p.get("name", ""))
            if len(variants) > 1:
                options = "\n".join([f"{i+1}. {v.get('name')}" for i, v in enumerate(variants)])
                return f"¿Qué presentación de {base_name} desea?\n{options}"

        # Missing quantity?
        if qty == 1 and not explicit_qty:
            return f"¿Cuántas unidades desea de {product.get('name')}?"

        # Stock check
        stock = product.get("stock", 0)
        if qty > stock:
            return f"Lo siento, solo hay {stock} unidades de {product.get('name')} disponibles. ¿Desea esa cantidad?"

    # Check delivery date (shared across all items)
    any_delivery = any(itm["delivery"] for itm in order_items)
    if not any_delivery:
        if len(order_items) == 1:
            return f"¿Para qué fecha desea la entrega de {order_items[0]['qty']} unidades de {order_items[0]['product'].get('name')}?"
        return "¿Para qué fecha desea la entrega?"

    # ── All complete: build confirmation ──
    if len(order_items) == 1:
        itm = order_items[0]
        return f"Orden recibida: {itm['qty']} unidades de {itm['product'].get('name')} para {itm['delivery']}."

    lines = ["Orden recibida:"]
    for itm in order_items:
        delivery = itm["delivery"] or global_delivery or "sin fecha"
        lines.append(f"- {itm['qty']} unidades de {itm['product'].get('name')} para {delivery}")
    return "\n".join(lines)


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
