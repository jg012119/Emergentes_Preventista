"""Order routes: draft creation, confirmation, listing and status changes."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import get_supabase_admin
from app.models.schemas import (
    OrderDraftRequest, OrderOut, OrderItemOut, OrderStatusUpdate,
)
from app.utils.auth import get_current_user_id
from app.services.notification_service import notify_status_change

router = APIRouter(prefix="/orders", tags=["orders"])

VALID_STATUSES = {"pendiente", "confirmado", "rechazado", "en_proceso"}


def _enrich_order(order: dict, db) -> OrderOut:
    """Add items and store_name to an order dict."""
    # Get items
    items_result = db.table("order_items").select("*").eq("order_id", order["id"]).execute()
    items = []
    for item in items_result.data:
        # Get product name
        prod = db.table("products").select("name").eq("id", item["product_id"]).execute()
        product_name = prod.data[0]["name"] if prod.data else "Desconocido"
        items.append(OrderItemOut(
            id=item["id"],
            order_id=item["order_id"],
            product_id=item["product_id"],
            product_name=product_name,
            quantity=item["quantity"],
            unit_price=item["unit_price"],
            subtotal=item["subtotal"],
        ))

    # Get store name
    store = db.table("stores").select("name").eq("id", order["store_id"]).execute()
    store_name = store.data[0]["name"] if store.data else "Desconocida"

    return OrderOut(
        id=order["id"],
        user_id=order["user_id"],
        store_id=order["store_id"],
        store_name=store_name,
        status=order["status"],
        delivery_date=str(order.get("delivery_date", "")) if order.get("delivery_date") else None,
        total=order["total"],
        notes=order.get("notes"),
        created_at=order.get("created_at"),
        items=items,
    )


@router.post("/draft", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_draft(body: OrderDraftRequest, user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()

    # Verify store belongs to user
    store = db.table("stores").select("id").eq("id", body.store_id).eq("user_id", user_id).execute()
    if not store.data:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")

    # Validate products & stock, compute total
    total = 0.0
    items_to_insert = []
    for item in body.items:
        prod_result = db.table("products").select("*").eq("id", item.product_id).eq("active", True).execute()
        if not prod_result.data:
            raise HTTPException(status_code=400, detail=f"Producto {item.product_id} no encontrado o inactivo")

        product = prod_result.data[0]
        if product["stock"] < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para {product['name']}. Disponible: {product['stock']}, Solicitado: {item.quantity}",
            )

        subtotal = product["price"] * item.quantity
        total += subtotal
        items_to_insert.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_price": product["price"],
            "subtotal": subtotal,
        })

    # Create order
    order_result = db.table("orders").insert({
        "user_id": user_id,
        "store_id": body.store_id,
        "status": "borrador",
        "delivery_date": str(body.delivery_date),
        "total": total,
        "notes": body.notes,
    }).execute()

    if not order_result.data:
        raise HTTPException(status_code=500, detail="Error al crear el pedido")

    order = order_result.data[0]

    # Insert order items
    for item_data in items_to_insert:
        item_data["order_id"] = order["id"]
    db.table("order_items").insert(items_to_insert).execute()

    # Add system message to chat
    db.table("chat_messages").insert({
        "user_id": user_id,
        "order_id": order["id"],
        "message": f"Pedido borrador creado. Total: Bs {total:.2f}. Confirma para enviarlo a AJE.",
        "sender": "system",
    }).execute()

    return _enrich_order(order, db)


@router.post("/{order_id}/confirm", response_model=OrderOut)
async def confirm_order(order_id: str, user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()

    # Get order
    result = db.table("orders").select("*").eq("id", order_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    order = result.data[0]
    if order["status"] != "borrador":
        raise HTTPException(status_code=400, detail="Solo se pueden confirmar pedidos en estado borrador")

    # Revalidate stock
    items = db.table("order_items").select("*").eq("order_id", order_id).execute()
    for item in items.data:
        prod = db.table("products").select("stock, name").eq("id", item["product_id"]).execute()
        if prod.data and prod.data[0]["stock"] < item["quantity"]:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para {prod.data[0]['name']}",
            )

    # Reduce stock
    for item in items.data:
        prod = db.table("products").select("stock").eq("id", item["product_id"]).execute()
        new_stock = prod.data[0]["stock"] - item["quantity"]
        db.table("products").update({"stock": new_stock}).eq("id", item["product_id"]).execute()

    # Update status
    updated = db.table("orders").update({"status": "pendiente"}).eq("id", order_id).execute()

    # Chat message
    db.table("chat_messages").insert({
        "user_id": user_id,
        "order_id": order_id,
        "message": "Tu pedido fue enviado correctamente a AJE y se encuentra en estado Pendiente. Te notificaremos por este chat y por correo cuando la empresa lo revise.",
        "sender": "system",
    }).execute()

    return _enrich_order(updated.data[0], db)


@router.get("/", response_model=list[OrderOut])
async def list_orders(
    status_filter: str | None = None,
    user_id: str = Depends(get_current_user_id),
):
    db = get_supabase_admin()
    query = db.table("orders").select("*").order("created_at", desc=True)

    # Check if user is admin (has role field) – for now treat all as their own orders
    # Panel will use /orders/all endpoint
    query = query.eq("user_id", user_id)
    if status_filter:
        query = query.eq("status", status_filter)

    result = query.execute()
    return [_enrich_order(o, db) for o in result.data]


@router.get("/all", response_model=list[OrderOut])
async def list_all_orders(
    status_filter: str | None = None,
    _user_id: str = Depends(get_current_user_id),
):
    """Admin/AJE endpoint – list all orders from all users."""
    db = get_supabase_admin()
    query = db.table("orders").select("*").order("created_at", desc=True)
    if status_filter:
        query = query.eq("status", status_filter)
    result = query.execute()
    return [_enrich_order(o, db) for o in result.data]


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: str, _user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    result = db.table("orders").select("*").eq("id", order_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return _enrich_order(result.data[0], db)


@router.put("/{order_id}/status", response_model=OrderOut)
async def update_order_status(
    order_id: str,
    body: OrderStatusUpdate,
    _user_id: str = Depends(get_current_user_id),
):
    """AJE changes order status and triggers notifications."""
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Opciones: {VALID_STATUSES}")

    db = get_supabase_admin()
    result = db.table("orders").select("*").eq("id", order_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    old_order = result.data[0]
    old_status = old_order["status"]

    # If rejecting, restore stock
    if body.status == "rechazado" and old_status in ("pendiente", "confirmado", "en_proceso"):
        items = db.table("order_items").select("*").eq("order_id", order_id).execute()
        for item in items.data:
            prod = db.table("products").select("stock").eq("id", item["product_id"]).execute()
            if prod.data:
                new_stock = prod.data[0]["stock"] + item["quantity"]
                db.table("products").update({"stock": new_stock}).eq("id", item["product_id"]).execute()

    updated = db.table("orders").update({"status": body.status}).eq("id", order_id).execute()

    # Notify user
    await notify_status_change(db, old_order, body.status)

    return _enrich_order(updated.data[0], db)
