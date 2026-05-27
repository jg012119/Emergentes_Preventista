"""User profile routes."""

from fastapi import APIRouter, Depends, HTTPException

from app.config import get_supabase_admin
from app.models.schemas import UserOut, UserUpdate
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    result = db.table("users").select("*").eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    u = result.data[0]
    return UserOut(
        id=u["id"], name=u["name"], email=u["email"],
        phone=u["phone"], created_at=u.get("created_at"),
    )


@router.get("/clients")
async def list_clients(_user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    users = db.table("users").select("*").order("created_at", desc=True).execute().data
    stores = db.table("stores").select("*").order("created_at", desc=True).execute().data
    orders = db.table("orders").select("*").order("created_at", desc=True).execute().data
    items = db.table("order_items").select("*").execute().data

    stores_by_user: dict[str, list[dict]] = {}
    for store in stores:
        stores_by_user.setdefault(store["user_id"], []).append(store)

    item_count_by_order: dict[str, int] = {}
    for item in items:
        order_id = item.get("order_id")
        if order_id:
            item_count_by_order[order_id] = item_count_by_order.get(order_id, 0) + 1

    store_name_by_id = {store["id"]: store["name"] for store in stores}
    orders_by_user: dict[str, list[dict]] = {}
    for order in orders:
        user_orders = orders_by_user.setdefault(order["user_id"], [])
        user_orders.append({
            "id": order["id"],
            "store_id": order.get("store_id"),
            "store_name": store_name_by_id.get(order.get("store_id"), "Desconocida"),
            "status": order.get("status"),
            "delivery_date": str(order.get("delivery_date")) if order.get("delivery_date") else None,
            "total": order.get("total", 0),
            "items_count": item_count_by_order.get(order["id"], 0),
            "created_at": order.get("created_at"),
        })

    clients = []
    for user in users:
        if user.get("role") == "admin":
            continue
        client_stores = stores_by_user.get(user["id"], [])
        client_orders = orders_by_user.get(user["id"], [])
        closed_orders = [order for order in client_orders if order.get("status") in {"confirmado", "rechazado"}]
        confirmed_orders = [order for order in client_orders if order.get("status") == "confirmado"]
        clients.append({
            "id": user["id"],
            "name": user.get("name", ""),
            "email": user.get("email", ""),
            "phone": user.get("phone", ""),
            "created_at": user.get("created_at"),
            "stores": client_stores,
            "orders": client_orders,
            "metrics": {
                "stores": len(client_stores),
                "orders": len(client_orders),
                "closed_orders": len(closed_orders),
                "confirmed_orders": len(confirmed_orders),
                "total_value": round(sum(float(order.get("total") or 0) for order in client_orders), 2),
            },
        })
    return clients


@router.put("/me", response_model=UserOut)
async def update_me(body: UserUpdate, user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")

    result = db.table("users").update(updates).eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    u = result.data[0]
    return UserOut(
        id=u["id"], name=u["name"], email=u["email"],
        phone=u["phone"], created_at=u.get("created_at"),
    )
