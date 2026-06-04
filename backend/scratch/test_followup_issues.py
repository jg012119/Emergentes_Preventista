import sys
from pathlib import Path

sys.path.append(str(Path("/home/jairomgr/Proyectos/expo/Emergentes_Preventista/backend")))

from app.config import get_supabase_admin
from app.routes.chat import _build_chat_reply
from app.models.schemas import ChatMessageCreate

db = get_supabase_admin()

# Get Jairo's user ID
res = db.table("users").select("id").eq("email", "jg012119@gmail.com").execute()
user_id = res.data[0]["id"]

# Create a clean draft order first for testing
# (Let's make sure we start from a clean state)
# We can find or create a draft. Let's delete existing drafts for this user first
# to avoid interference, then create one.
try:
    db.table("orders").delete().eq("user_id", user_id).eq("status", "borrador").execute()
except Exception:
    pass

print("=== 1. TESTING AUTO-ACCEPT FOR 'Quiero 2 aguas de 500 para mañana' ===")
body = ChatMessageCreate(
    message="Quiero 2 aguas de 500 para mañana",
    sender="user",
    context={}
)
reply = _build_chat_reply(db, user_id, body)
print("Reply:")
print(reply)

# Find the order ID created by the auto-accept
res_order = db.table("orders").select("id").eq("user_id", user_id).eq("status", "borrador").order("created_at", desc=True).limit(1).execute()
active_order_id = res_order.data[0]["id"] if res_order.data else None
print("\nCreated active order ID:", active_order_id)

print("\n=== 2. TESTING ADDING 'Agua' -> '1l' -> '8' TO ACTIVE ORDER ===")
# User sends "Agua" in context of active_order_id
body = ChatMessageCreate(
    message="Agua",
    sender="user",
    order_id=active_order_id,
    context={"active_order_id": active_order_id}
)
reply = _build_chat_reply(db, user_id, body)
print("Reply to 'Agua':")
print(reply)

# Simulate reply "1l" to clarification
body = ChatMessageCreate(
    message="1l",
    sender="user",
    order_id=active_order_id,
    context={"active_order_id": active_order_id}
)
reply = _build_chat_reply(db, user_id, body)
print("\nReply to '1l':")
print(reply)

# Simulate reply "8" to quantity clarification
body = ChatMessageCreate(
    message="8",
    sender="user",
    order_id=active_order_id,
    context={"active_order_id": active_order_id}
)
reply = _build_chat_reply(db, user_id, body)
print("\nReply to '8':")
print(reply)

# Double check final order status and items
if active_order_id:
    order_res = db.table("orders").select("*").eq("id", active_order_id).execute().data[0]
    items_res = db.table("order_items").select("*").eq("order_id", active_order_id).execute().data
    print("\n--- FINAL ORDER IN DB ---")
    print("Order ID:", order_res["id"])
    print("Total:", order_res["total"])
    print("Items:")
    for item in items_res:
        prod = db.table("products").select("name").eq("id", item["product_id"]).execute().data[0]["name"]
        print(f"  - {item['quantity']} x {prod} (Bs {item['unit_price']}) = Bs {item['subtotal']}")
