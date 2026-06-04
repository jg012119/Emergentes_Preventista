import sys
from pathlib import Path

sys.path.append(str(Path("/home/jairomgr/Proyectos/expo/Emergentes_Preventista/backend")))

from app.config import get_supabase_admin
from app.routes.chat import _build_chat_reply
from app.models.schemas import ChatMessageCreate

db = get_supabase_admin()
res = db.table("users").select("id").eq("email", "jg012119@gmail.com").execute()
user_id = res.data[0]["id"]

# Clean drafts
try:
    db.table("orders").delete().eq("user_id", user_id).eq("status", "borrador").execute()
except Exception:
    pass

# We will send a typo "2 ccas de 2l para mañana"
# This will have a low score for brand, but wait!
# If brand is "ccas", spelling variants: "ccas".
# "ccas" vs "coca cola": "coca" contains c, c, a.
# Let's see if it triggers confirmation.
print("=== TESTING TYPO AND AFFIRMATION 'Si' ===")

body = ChatMessageCreate(
    message="2 ccas de 2l para mañana",
    sender="user",
    context={}
)
reply = _build_chat_reply(db, user_id, body)
print("Reply to '2 ccas de 2l para mañana':")
print(reply)

# Find active order or interaction
res_order = db.table("orders").select("id").eq("user_id", user_id).eq("status", "borrador").order("created_at", desc=True).limit(1).execute()
active_order_id = res_order.data[0]["id"] if res_order.data else None

# Send "Si"
body = ChatMessageCreate(
    message="Si",
    sender="user",
    order_id=active_order_id,
    context={"active_order_id": active_order_id}
)
reply = _build_chat_reply(db, user_id, body)
print("\nReply to 'Si':")
print(reply)
