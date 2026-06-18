import sys
from pathlib import Path

sys.path.append(str(Path("/home/jairomgr/Proyectos/expo/Emergentes_Preventista/backend")))

from app.config import get_supabase_admin
from app.routes.nlp import _parse_order_payload, draft_order_chat_reply, _is_clarification_reply, _matching_pending_clarification, _interpret_clarification_reply

db = get_supabase_admin()

# Let's get a real user ID. We can select the first user from the database.
user_row = db.table("users").select("id, email").limit(1).execute().data
if not user_row:
    print("No users found in DB")
    sys.exit(1)
user_id = user_row[0]["id"]
email = user_row[0]["email"]
print(f"Testing with user: {email} ({user_id})")

# Test 1: "un agua de un litro"
print("\n--- Test 1: 'un agua de un litro' ---")
parsed = _parse_order_payload(db, text="un agua de un litro", user_id=user_id, persist=False)
print("Requires clarification:", parsed.requires_clarification)
print("Validation status:", parsed.validation_status)
print("Message:")
print(parsed.message)
for item in parsed.items:
    print(f"Item: {item.raw_text}")
    print(f"  Detected: {item.producto_detectado}, normalized: {item.producto_normalizado}")
    print(f"  Presentation: {item.presentacion}")
    print(f"  Candidates:")
    for c in item.sku_candidates:
        print(f"    - {c.product} ({c.presentation}) score: {c.score}")

# Test 2: "Volt 5, agua 7 y 1 coca cola"
print("\n--- Test 2: 'Volt 5, agua 7 y 1 coca cola' ---")
from app.routes.nlp import _split_order_segments
segments = _split_order_segments("Volt 5, agua 7 y 1 coca cola")
print("Segments split:", segments)
parsed2 = _parse_order_payload(db, text="Volt 5, agua 7 y 1 coca cola", user_id=user_id, persist=False)
print("Requires clarification:", parsed2.requires_clarification)
print("Validation status:", parsed2.validation_status)
print("Message:")
print(parsed2.message)
for item in parsed2.items:
    print(f"Item: {item.raw_text}")
    print(f"  Detected: {item.producto_detectado}, normalized: {item.producto_normalizado}")
    print(f"  Presentation: {item.presentacion}")
    print(f"  Candidates:")
    for c in item.sku_candidates:
        print(f"    - {c.product} ({c.presentation}) score: {c.score}")

