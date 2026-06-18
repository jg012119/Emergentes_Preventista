import sys
from pathlib import Path

sys.path.append(str(Path("/home/jairomgr/Proyectos/expo/Emergentes_Preventista/backend")))

from app.config import get_supabase_admin
from app.routes.nlp import draft_order_chat_reply, _parse_order_payload

db = get_supabase_admin()

# Get first user
user_row = db.table("users").select("id, email").limit(1).execute().data
if not user_row:
    print("No users found in DB")
    sys.exit(1)
user_id = user_row[0]["id"]
email = user_row[0]["email"]
print(f"Testing with user: {email} ({user_id})")

# Clear any active drafts and clarification events for clean state
db.table("orders").delete().eq("user_id", user_id).eq("status", "borrador").execute()
db.table("clarification_events").delete().eq("user_id", user_id).execute()

# Step 1: User says: "Volt chico, agua chica y coca de 2 litros"
msg1 = "Volt chico, agua chica y coca de 2 litros"
print(f"\n--- User Step 1: '{msg1}' ---")
reply1 = draft_order_chat_reply(
    db,
    text=msg1,
    user_id=user_id,
    requested_store_id=None,
    active_order_id=None,
)
print("Bot response:")
print(reply1)

# Step 2: User replies: "Volt 5, agua 7 y 1 coca cola"
msg2 = "Volt 5, agua 7 y 1 coca cola"
print(f"\n--- User Step 2: '{msg2}' ---")
reply2 = draft_order_chat_reply(
    db,
    text=msg2,
    user_id=user_id,
    requested_store_id=None,
    active_order_id=None,
)
print("Bot response:")
print(reply2)
