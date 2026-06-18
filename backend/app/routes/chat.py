"""Chat message routes."""

import json
import logging
import re
import unicodedata
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException

from app.config import get_supabase_admin
from app.models.schemas import ChatFeedbackOut, ChatFeedbackRequest, ChatMessageCreate, ChatMessageOut
from app.routes.orders import confirm_order_in_db
from app.routes.nlp import draft_order_chat_reply
from app.services.llm import ask_llm
from app.services.product_resolver import resolve_all_products
from app.utils.auth import get_current_user_id

logger = logging.getLogger(__name__)

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
CONFIRMATION_WORDS = {
    "si", "ok", "okay", "dale", "confirmar", "pagar", "acabar",
    "listo", "terminar", "finalizar", "finaliza", "finalizo",
    "confirmo", "confirmado", "confirmar pedido", "enviar", "enviar pedido",
    "perfecto", "esta perfecto", "esta bien", "todo bien", "correcto",
}
FINALIZATION_COMMANDS = CONFIRMATION_WORDS - {"si", "ok", "okay", "dale"}


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


_ORDER_KEYWORDS = {
    "coca", "cola", "cielo", "agua", "volt", "oro", "pulp", "cifrut", "sporade", "tea", "free",
    "litro", "litros", "ml", "personal", "familiar", "chica", "chico", "grande", "lata", "caja",
    "un", "una", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez", "docena"
}


def _contains_order_indications(text: str) -> bool:
    if any(char.isdigit() for char in text):
        return True
    words = [w.strip(".,!?()-\"'/") for w in text.lower().split()]
    return any(word in _ORDER_KEYWORDS for word in words)


def _is_confirmation_message(text: str) -> bool:
    if not text:
        return False
    
    words = [w.strip(".,!?()-\"'/") for w in text.lower().split()]
    words = [w for w in words if w]
    if not words:
        return False
        
    if any(neg in words for neg in ("no", "tampoco", "nunca", "jamas", "sin")):
        return False
        
    if _contains_order_indications(text):
        return False
        
    normalized = " ".join(words)
    if normalized in CONFIRMATION_WORDS:
        return True
        
    if len(words) <= 3 and any(w in CONFIRMATION_WORDS for w in words):
        return True
        
    return False


def _is_finalization_command(text: str) -> bool:
    return bool(text and text in FINALIZATION_COMMANDS)


def get_active_session_state(db, user_id: str) -> dict | None:
    """Get active chat session state, clearing it if it has expired."""
    try:
        res = db.table("chat_session_state").select("*").eq("user_id", user_id).execute().data
        if not res:
            return None
        state = res[0]
        expires_at_str = state.get("expires_at")
        if expires_at_str:
            if expires_at_str.endswith("Z"):
                expires_at_str = expires_at_str[:-1] + "+00:00"
            expires_at = datetime.fromisoformat(expires_at_str)
            if expires_at < datetime.now(timezone.utc):
                db.table("chat_session_state").delete().eq("user_id", user_id).execute()
                return None
        return state
    except Exception as exc:
        logger.warning("Error getting chat session state: %s", exc)
        return None


def save_chat_session_state(db, user_id: str, payload: dict) -> None:
    """Save or update chat session state, setting a 10-minute expiry."""
    try:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        payload["expires_at"] = expires_at.isoformat()
        payload["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        existing = db.table("chat_session_state").select("user_id").eq("user_id", user_id).execute().data
        if existing:
            db.table("chat_session_state").update(payload).eq("user_id", user_id).execute()
        else:
            payload["user_id"] = user_id
            db.table("chat_session_state").insert(payload).execute()
    except Exception as exc:
        logger.warning("Error saving chat session state: %s", exc)


def clear_chat_session_state(db, user_id: str) -> None:
    """Clear chat session state for the user."""
    try:
        db.table("chat_session_state").delete().eq("user_id", user_id).execute()
    except Exception as exc:
        logger.warning("Error clearing chat session state: %s", exc)


def _confirm_active_order_message(db, user_id: str, active_order_id: str | None) -> str:
    if not active_order_id:
        return (
            "Aun no tengo un borrador listo para enviar. "
            "Primero armemos el pedido con productos, tienda y fecha de entrega."
        )

    try:
        order = confirm_order_in_db(
            db,
            order_id=active_order_id,
            user_id=user_id,
            add_chat_message=False,
        )
        clear_chat_session_state(db, user_id)
    except HTTPException as exc:
        return str(exc.detail)

    lines = [
        f"Pedido #{order.id[:8]} confirmado y enviado a AJE.",
        "Estado: Pendiente.",
        f"Tienda: {order.store_name or 'Sin tienda'}",
        f"Entrega: {order.delivery_date or 'sin fecha'}",
        f"Total: {_money(order.total)}",
        "Ya puedes verlo en tu lista de pedidos pendientes.",
        _action_line(_order_action(db, order.model_dump())),
    ]
    return "\n".join(lines)


def _save_latest_draft_to_session(db, user_id: str) -> None:
    try:
        latest_draft = db.table("orders").select("id").eq("user_id", user_id).eq("status", "borrador").order("created_at", desc=True).limit(1).execute().data
        if latest_draft:
            save_chat_session_state(db, user_id, {"active_order_id": latest_draft[0]["id"]})
    except Exception as exc:
        logger.warning("Failed to save latest draft to session: %s", exc)


def _confirm_pending_order_text_message(db, user_id: str, pending_order_text: str) -> str:
    from app.routes.nlp import _parse_order_payload
    try:
        parsed = _parse_order_payload(
            db,
            text=pending_order_text,
            user_id=user_id,
            require_store=True,
            persist=False,
        )
    except Exception as exc:
        logger.warning("Failed to parse pending order text during confirmation: %s", exc)
        return (
            "Aun no tengo un borrador listo para enviar. "
            "Primero armemos el pedido con productos, tienda y fecha de entrega."
        )

    valid_items = [item for item in parsed.items if item.sku_id or item.product_id]
    if not valid_items:
        return (
            "Aun no tengo un borrador listo para enviar. "
            "Primero armemos el pedido con productos, tienda y fecha de entrega."
        )

    lines = ["Tengo anotados estos productos para tu pedido:"]
    for item in valid_items:
        lines.append(f"- {item.cantidad} x {item.producto_normalizado or item.producto_detectado}")

    missing = []
    if not parsed.store_id:
        missing.append("la tienda (ej. 'tienda Don Bosco' o 'mi tienda')")
    if not parsed.fecha_entrega:
        missing.append("la fecha de entrega (ej. 'para mañana' o 'para el viernes')")

    if missing:
        missing_str = " y ".join(missing)
        lines.append(f"\nPero para poder guardarlo y enviarlo, por favor indícame {missing_str}.")
    else:
        lines.append("\nTodo parece listo. Por favor confirma el pedido.")

    return "\n".join(lines)


def _build_chat_reply(db, user_id: str, body: ChatMessageCreate) -> str | None:
    if _is_structured_order_message(body.message):
        return None

    text = _normalize_text(body.message)
    status_filter = _find_status_filter(text)

    if text in _PURE_NEGATION_NORMALIZED:
        clear_chat_session_state(db, user_id)
        return "Entendido, sin problema. Avisame cuando necesites algo."

    # Load session state to retrieve active order ID if missing
    session_state = get_active_session_state(db, user_id)
    session_active_order_id = session_state.get("active_order_id") if session_state else None
    active_order_id = body.order_id or (body.context or {}).get("active_order_id") or session_active_order_id

    pending_order_text = (body.context or {}).get("pending_order_text")

    if _is_confirmation_message(text):
        if active_order_id:
            return _confirm_active_order_message(db, user_id, active_order_id)
        if pending_order_text:
            return _confirm_pending_order_text_message(db, user_id, pending_order_text)

    if _is_finalization_command(text):
        if active_order_id:
            return _confirm_active_order_message(db, user_id, active_order_id)
        if pending_order_text:
            return _confirm_pending_order_text_message(db, user_id, pending_order_text)
        return _confirm_active_order_message(db, user_id, active_order_id)

    if "menu" in text or "catalogo" in text or "productos" in text:
        return _build_product_menu(db, user_id)

    if "estado" in text or "seguimiento" in text or "como va" in text:
        return _order_status_message(db, user_id, body.order_id or active_order_id)

    if "lista" in text or "ordenes" in text:
        return _list_orders_message(db, user_id, status_filter)

    if status_filter:
        return _list_orders_message(db, user_id, status_filter)

    # Handle "no quiero X, solo Y" → redirect to "Y" as the new request
    redirect_text = _get_redirect_text(body.message)
    if redirect_text:
        # Build NLP reply with just the redirected product text
        nlp_reply = draft_order_chat_reply(
            db,
            text=redirect_text,
            user_id=user_id,
            requested_store_id=None,
            active_order_id=active_order_id,
            context=body.context,
        )
        if nlp_reply:
            _save_latest_draft_to_session(db, user_id)
            return nlp_reply

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
        _save_latest_draft_to_session(db, user_id)
        return nlp_reply

    if _is_confirmation_message(text):
        if active_order_id:
            return _confirm_active_order_message(db, user_id, active_order_id)
        if pending_order_text:
            return _confirm_pending_order_text_message(db, user_id, pending_order_text)

    if "pedido" in text or "pedidos" in text:
        return _list_orders_message(db, user_id, status_filter)

    # ------------------------------------------------------------------
    # LLM fallback: ask Ollama when rule-based NLP couldn't resolve
    # ------------------------------------------------------------------
    return None  # signal to the async handler to try LLM


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



async def _llm_fallback_reply(db, user_id: str, message: str) -> str | None:
    """Call Ollama when the rule-based NLP couldn't resolve the user message.

    Flow:
    1. Load catalog + aliases from DB
    2. Load last 6 messages as conversation history
    3. Call ask_llm() → get a validated LlamaIntent object
    4. For 'pedido': run product_resolver to validate each product against real DB
       - All matched → create a real draft via draft_order_chat_reply()
       - Ambiguous products → ask clarification question
       - Not found → show ❓ message
    5. For other intents: return appropriate response

    Never writes orders directly — always goes through draft_order_chat_reply()
    so the confirmation flow is preserved.
    """
    try:
        # Load active products
        products = (
            db.table("products")
            .select("id, name, price, stock, category")
            .eq("active", True)
            .execute()
            .data or []
        )

        # Load aliases for richer resolution
        try:
            aliases = (
                db.table("product_aliases")
                .select("product_id, alias_text, normalized_alias, confidence_weight")
                .execute()
                .data or []
            )
        except Exception:
            aliases = []

        # Build short conversation history so the model has context
        recent_msgs = (
            db.table("chat_messages")
            .select("message, sender")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(6)
            .execute()
            .data or []
        )
        history = [
            {
                "role": "user" if m["sender"] == "user" else "assistant",
                "content": m["message"],
            }
            for m in reversed(recent_msgs)
            if m.get("message")
        ]

        result = await ask_llm(message, products, history, user_id=user_id)
    except Exception as exc:
        logger.warning("LLM fallback error: %s", exc)
        return None

    if result is None:
        return None

    intencion = result.intencion

    # --- Saludo ---
    if intencion == "saludo":
        return result.mensaje_libre or "¡Hola! 😊 Soy tu asistente AJE. ¿Qué bebidas te envío hoy?"

    # --- Negación ---
    if intencion == "negacion":
        return result.mensaje_libre or "Entendido, sin problema. Avisame cuando necesites algo."

    # --- Consulta de catálogo ---
    if intencion in ("consulta_catalogo", "listar_pedidos", "estado_pedido"):
        if intencion == "consulta_catalogo":
            return _build_product_menu(db, user_id)
        # Para listar/estado → dejar que Capa 1 lo maneje en el siguiente mensaje
        return result.mensaje_libre or "Puedo mostrarte tus pedidos. Escribe ‘lista de pedidos’ o ‘estado’."

    # --- Fuera de alcance (sólidos / alcohol) ---
    if intencion == "fuera_de_alcance":
        motivo = result.motivo_rechazo or ""
        if result.mensaje_libre:
            return result.mensaje_libre
        if motivo == "alcohol":
            return "❌ Lamento informarte que no distribuimos bebidas alcohólicas."
        if motivo == "comida_solida":
            return (
                "❌ Lamento informarte que no contamos con ese producto, "
                "ya que nos especializamos exclusivamente en el abastecimiento "
                "de productos líquidos y bebidas."
            )
        return result.mensaje_libre or "Lo siento, ese producto está fuera de nuestro catálogo."

    # --- Pedido detectado --- usar product_resolver y crear borrador real ---
    if intencion == "pedido" and result.productos:
        resolved = resolve_all_products(result.productos, products, aliases)

        all_matched = all(r.status == "matched" for r in resolved)
        any_ambiguous = any(r.status == "ambiguous" for r in resolved)
        any_not_found = any(r.status == "not_found" for r in resolved)

        # Build the confirmation summary lines
        lines: list[str] = []
        for llm_prod, res in zip(result.productos, resolved):
            if res.status == "matched":
                lines.append(
                    f"✅ *{llm_prod.texto_original}* → **{res.product_name}** "
                    f"x{res.quantity} — Bs {res.product_price:.2f} c/u"
                )
            elif res.status == "ambiguous":
                opts = ", ".join(o["name"] for o in res.options[:4])
                lines.append(
                    f"❓ *{llm_prod.texto_original}* — {res.clarification_question or f'¿Cuál versión quieres? Opciones: {opts}'}"
                )
            else:  # not_found
                lines.append(
                    f"❌ *{llm_prod.texto_original}* — No encontré ese producto en el catálogo. "
                    "Escribe ‘menu’ para ver los disponibles."
                )

        if any_ambiguous:
            # Need clarification before creating draft
            ambig = next(r for r in resolved if r.status == "ambiguous")
            return "\n".join(lines) + (
                f"\n\n{ambig.clarification_question}"
                if ambig.clarification_question else ""
            )

        if any_not_found and not all_matched:
            # Some not found — show summary, don't create draft
            lines.append("\nEscribe ‘menu’ para ver todos los productos disponibles.")
            return "\n".join(lines)

        if all_matched:
            # ALL products resolved → build text for draft_order_chat_reply
            # Construct a normalized text that the NLP parser can use
            order_parts = []
            for res in resolved:
                order_parts.append(f"{res.quantity} {res.product_name}")
            synthetic_text = ", ".join(order_parts)

            # Add delivery date if LLM detected it
            if result.fecha_entrega:
                synthetic_text += f" para {result.fecha_entrega}"

            logger.info(
                "LLM resolved all products, creating draft via NLP. synthetic_text=%r",
                synthetic_text,
            )

            nlp_reply = draft_order_chat_reply(
                db,
                text=synthetic_text,
                user_id=user_id,
                requested_store_id=None,
                active_order_id=None,
                context=None,
            )
            if nlp_reply:
                return nlp_reply

            # NLP couldn't process the synthetic text either — show product list
            total = sum((r.product_price or 0) * r.quantity for r in resolved if r.status == "matched")
            lines.append(f"\nTotal estimado: Bs {total:.2f}")
            lines.append("\n¿Confirmamos el pedido con estos productos?")
            return "\n".join(lines)

    # --- Ambiguo o no clasificado ---
    if result.requiere_aclaracion and result.pregunta_aclaracion:
        return result.pregunta_aclaracion

    if result.mensaje_libre:
        return result.mensaje_libre

    return None


@router.post("/message", response_model=ChatMessageOut, status_code=201)
async def send_message(body: ChatMessageCreate, user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    
    raw_message = body.message
    # Si viene de nota de voz, parsear JSON y extraer texto para el agente
    try:
        import json
        parsed = json.loads(raw_message)
        if isinstance(parsed, dict) and parsed.get("is_voice"):
            body.message = parsed.get("text", "")
    except Exception:
        pass

    result = db.table("chat_messages").insert({
        "user_id": user_id,
        "order_id": body.order_id,
        "message": raw_message,
        "sender": body.sender,
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Error al enviar mensaje")

    reply: str | None = None
    if body.sender == "user":
        # 1. Fast rule-based NLP (synchronous)
        reply = _build_chat_reply(db, user_id, body)

        # 2. LLM fallback if NLP returned nothing
        if reply is None:
            reply = await _llm_fallback_reply(db, user_id, body.message)

        # 3. Generic fallback if Ollama is also unavailable
        if reply is None:
            reply = (
                "Puedo ayudarte con: menú de productos, estado del pedido, "
                "lista de pedidos, pedidos pendientes, confirmados, rechazados, "
                "en proceso o pagados."
            )

    if reply:
        session_state = get_active_session_state(db, user_id)
        current_active_order_id = session_state.get("active_order_id") if session_state else None
        order_id = body.order_id or current_active_order_id

        db.table("chat_messages").insert({
            "user_id": user_id,
            "order_id": order_id,
            "message": reply,
            "sender": "empresa",
        }).execute()

        if order_id and not body.order_id:
            try:
                db.table("chat_messages").update({"order_id": order_id}).eq("id", result.data[0]["id"]).execute()
                result.data[0]["order_id"] = order_id
            except Exception:
                pass

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
    
    general_messages = result.data or []
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
