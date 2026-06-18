import sys
from pathlib import Path

sys.path.append(str(Path("/home/jairomgr/Proyectos/expo/Emergentes_Preventista/backend")))

from app.config import get_supabase_admin

db = get_supabase_admin()

email = "jg012119@gmail.com"
print(f"--- FETCHING CHAT FOR: {email} ---")

try:
    # 1. Get user ID
    user_res = db.table("users").select("id, name").eq("email", email).execute()
    if not user_res.data:
        print(f"No user found with email {email}")
        sys.exit(1)
    
    user_id = user_res.data[0]["id"]
    user_name = user_res.data[0]["name"]
    print(f"User: {user_name} | ID: {user_id}")
    
    # 2. Get last 15 chat messages
    messages = (
        db.table("chat_messages")
        .select("id, message, sender, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(15)
        .execute()
        .data
        or []
    )
    
    print("\nLast 15 Chat Messages (Chronological Order):")
    for msg in reversed(messages):
        sender_label = "👤 USER" if msg["sender"] == "user" else "🤖 BOT"
        print(f"[{msg['created_at']}] {sender_label}: {msg['message']}")
        
    # 3. Get any pending clarifications
    clarifications = (
        db.table("clarification_events")
        .select("id, question_type, question_text, resolved, created_at")
        .eq("user_id", user_id)
        .eq("resolved", False)
        .execute()
        .data
        or []
    )
    if clarifications:
        print("\nUnresolved Clarifications:")
        for c in clarifications:
            print(f"  ID: {c['id']} | Type: {c['question_type']} | Msg: {c['question_text']}")
    else:
        print("\nNo unresolved clarifications.")
        
except Exception as e:
    print("Error querying database:", e)
