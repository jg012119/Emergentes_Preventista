import sys
from pathlib import Path

sys.path.append(str(Path("/home/jairomgr/Proyectos/expo/Emergentes_Preventista/backend")))

from app.config import get_supabase_admin

db = get_supabase_admin()

print("--- ALL PRODUCTS IN DATABASE ---")
try:
    res = db.table("products").select("id, name, active").execute()
    for row in res.data:
        print(f"ID: {row['id']} | Name: {row['name']} | Active: {row['active']}")
except Exception as e:
    print("Error querying products:", e)

print("\n--- ALL ALIASES IN DATABASE ---")
try:
    res = db.table("product_aliases").select("*").execute()
    for row in res.data:
        print(row)
except Exception as e:
    print("Error querying aliases:", e)
