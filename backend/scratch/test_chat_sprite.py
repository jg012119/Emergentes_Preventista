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

# Find the active order ID from the latest draft created for Jairo
res_order = db.table("orders").select("id").eq("user_id", user_id).eq("status", "borrador").order("created_at", desc=True).limit(1).execute()
active_order_id = res_order.data[0]["id"] if res_order.data else None
print("Active order ID:", active_order_id)

test_messages = [
    "Hola",
    "Quiero sprite de 2L",
    "Quiero big de 2l",
    "Me das 2 coca de 2l"
]

for msg in test_messages:
    body = ChatMessageCreate(
        message=msg,
        sender="user",
        context={
            "active_order_id": active_order_id
        }
    )
    reply = _build_chat_reply(db, user_id, body)
    print(f"\nUser: '{msg}'")
    # Clean action prefix for readability if present
    clean_reply = reply.split("@@action")[0].strip() if reply else ""
    print(f"Company: {clean_reply}")
