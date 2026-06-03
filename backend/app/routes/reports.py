"""Business reports for the preventista agent and admin panel."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends

from ..config import get_supabase_admin
from ..utils.auth import get_current_user_id

router = APIRouter(prefix="/reports", tags=["reports"])

AUTO_SENDERS = {"system", "empresa", "agent", "agente"}
CLOSED_STATUSES = {"confirmado", "rechazado", "pagado"}
OPEN_STATUSES = {"pendiente", "en_proceso"}


def _as_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _safe_percent(part: float, total: float) -> float:
    if not total:
        return 0.0
    return round((part / total) * 100, 1)


def _date_key(value: Any) -> str:
    if not value:
        return "Sin fecha"
    raw = str(value).strip()
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return raw[:10] if len(raw) >= 10 else "Sin fecha"


@router.get("/agent")
async def get_agent_report(_user_id: str = Depends(get_current_user_id)):
    """Return operational metrics focused on the preventista agent."""
    db = get_supabase_admin()

    orders = db.table("orders").select("*").order("created_at", desc=True).execute().data
    items = db.table("order_items").select("*").execute().data
    products = db.table("products").select("*").execute().data
    messages = db.table("chat_messages").select("*").order("created_at").execute().data
    notifications = db.table("notifications").select("*").execute().data
    stores = db.table("stores").select("*").execute().data
    users = db.table("users").select("*").execute().data

    orders_by_id = {o["id"]: o for o in orders}
    products_by_id = {p["id"]: p for p in products}
    stores_by_id = {s["id"]: s for s in stores}
    users_by_id = {u["id"]: u for u in users}

    status_counter = Counter(o.get("status", "sin_estado") for o in orders)
    auto_messages = [m for m in messages if str(m.get("sender", "")).lower() in AUTO_SENDERS]
    user_messages = [m for m in messages if str(m.get("sender", "")).lower() == "user"]
    order_messages = [m for m in messages if m.get("order_id")]
    general_messages = [m for m in messages if not m.get("order_id")]

    confirmed_orders = [o for o in orders if o.get("status") in {"confirmado", "pagado"}]
    rejected_orders = [o for o in orders if o.get("status") == "rechazado"]
    paid_orders = [o for o in orders if o.get("status") == "pagado"]
    closed_orders = [o for o in orders if o.get("status") in CLOSED_STATUSES]
    open_orders = [o for o in orders if o.get("status") in OPEN_STATUSES]
    draft_orders = [o for o in orders if o.get("status") == "borrador"]

    total_value = sum(_as_float(o.get("total")) for o in orders)
    confirmed_value = sum(_as_float(o.get("total")) for o in confirmed_orders)
    pipeline_value = sum(_as_float(o.get("total")) for o in open_orders)
    rejected_value = sum(_as_float(o.get("total")) for o in rejected_orders)

    orders_with_auto_message = {
        m.get("order_id")
        for m in auto_messages
        if m.get("order_id")
    }

    customers_touched = {
        entity.get("user_id")
        for entity in [*orders, *messages]
        if entity.get("user_id")
    }
    active_store_ids = {o.get("store_id") for o in orders if o.get("store_id")}

    messages_by_order = Counter(m.get("order_id") for m in order_messages if m.get("order_id"))
    avg_messages_per_order = round(sum(messages_by_order.values()) / len(messages_by_order), 1) if messages_by_order else 0

    orders_by_day = defaultdict(lambda: {"date": "", "orders": 0, "auto_messages": 0, "value": 0.0})
    for order in orders:
        key = _date_key(order.get("created_at"))
        orders_by_day[key]["date"] = key
        orders_by_day[key]["orders"] += 1
        orders_by_day[key]["value"] += _as_float(order.get("total"))
    for message in auto_messages:
        key = _date_key(message.get("created_at"))
        orders_by_day[key]["date"] = key
        orders_by_day[key]["auto_messages"] += 1

    client_summary = defaultdict(lambda: {"client_id": "", "client_name": "Cliente", "orders": 0, "value": 0.0, "closed": 0})
    for order in orders:
        user_id = order.get("user_id")
        if not user_id:
            continue
        user = users_by_id.get(user_id, {})
        row = client_summary[user_id]
        row["client_id"] = user_id
        row["client_name"] = user.get("name") or user.get("email") or "Cliente"
        row["orders"] += 1
        row["value"] += _as_float(order.get("total"))
        if order.get("status") in CLOSED_STATUSES:
            row["closed"] += 1

    store_summary = defaultdict(lambda: {"store_id": "", "store_name": "Sucursal", "orders": 0, "value": 0.0})
    for order in orders:
        store_id = order.get("store_id")
        if not store_id:
            continue
        store = stores_by_id.get(store_id, {})
        row = store_summary[store_id]
        row["store_id"] = store_id
        row["store_name"] = store.get("name") or "Sucursal"
        row["orders"] += 1
        row["value"] += _as_float(order.get("total"))

    product_summary = defaultdict(lambda: {"product_id": "", "product_name": "Producto", "quantity": 0, "value": 0.0, "orders": set()})
    for item in items:
        product_id = item.get("product_id")
        product = products_by_id.get(product_id, {})
        row = product_summary[product_id]
        row["product_id"] = product_id or ""
        row["product_name"] = product.get("name") or "Producto"
        row["quantity"] += _as_int(item.get("quantity"))
        row["value"] += _as_float(item.get("subtotal"))
        if item.get("order_id"):
            row["orders"].add(item["order_id"])

    top_products = []
    for row in product_summary.values():
        row["orders"] = len(row["orders"])
        top_products.append(row)

    notification_counter = Counter(n.get("status", "sin_estado") for n in notifications)

    return {
        "summary": {
            "orders_taken": len(orders),
            "orders_with_agent": len(orders_with_auto_message),
            "auto_messages": len(auto_messages),
            "user_messages": len(user_messages),
            "general_messages": len(general_messages),
            "customers_touched": len(customers_touched),
            "active_stores": len(active_store_ids),
            "avg_messages_per_order": avg_messages_per_order,
            "agent_share": _safe_percent(len(auto_messages), len(messages)),
        },
        "closing": {
            "closed_orders": len(closed_orders),
            "confirmed_orders": len(confirmed_orders),
            "rejected_orders": len(rejected_orders),
            "open_orders": len(open_orders),
            "draft_orders": len(draft_orders),
            "paid_orders": len(paid_orders),
            "close_rate": _safe_percent(len(confirmed_orders), len(closed_orders)),
        },
        "values": {
            "total_value": round(total_value, 2),
            "confirmed_value": round(confirmed_value, 2),
            "pipeline_value": round(pipeline_value, 2),
            "rejected_value": round(rejected_value, 2),
        },
        "status_breakdown": [
            {"status": status, "count": count}
            for status, count in status_counter.most_common()
        ],
        "notifications": {
            "total": len(notifications),
            "sent": notification_counter.get("enviado", 0),
            "pending": notification_counter.get("pendiente", 0),
            "failed": notification_counter.get("fallido", 0),
        },
        "timeline": sorted(orders_by_day.values(), key=lambda row: row["date"])[-14:],
        "top_clients": sorted(client_summary.values(), key=lambda row: row["value"], reverse=True)[:5],
        "top_stores": sorted(store_summary.values(), key=lambda row: row["value"], reverse=True)[:5],
        "top_products": sorted(top_products, key=lambda row: row["quantity"], reverse=True)[:6],
    }
