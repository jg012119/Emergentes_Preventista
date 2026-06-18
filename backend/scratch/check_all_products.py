import sys
from pathlib import Path

sys.path.append(str(Path("/home/jairomgr/Proyectos/expo/Emergentes_Preventista/backend")))

from app.config import get_supabase_admin

db = get_supabase_admin()

print("--- VOLT & COCA PRODUCTS & ALIASES IN SUPABASE ---")
try:
    res_p = db.table("products").select("id, name").execute()
    p_map = {row['id']: row['name'] for row in res_p.data}
    
    res_a = db.table("product_aliases").select("*").execute()
    for row in res_a.data:
        p_name = p_map.get(row['product_id'], "Unknown")
        if "volt" in p_name.lower() or "coca" in p_name.lower() or "volt" in row['alias_text'].lower() or "coca" in row['alias_text'].lower():
            print(f"Product: {p_name} | Alias: {row['alias_text']} | Confidence: {row['confidence_weight']}")
except Exception as e:
    print("Error querying database:", e)

