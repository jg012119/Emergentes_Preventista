import sys
from pathlib import Path

sys.path.append(str(Path("/home/jairomgr/Proyectos/expo/Emergentes_Preventista/backend")))

from app.config import get_supabase_admin
from app.routes.nlp import _clean_segment, _product_signal_text, _product_family, _spelling_variants
from rapidfuzz import fuzz

db = get_supabase_admin()
products = db.table("products").select("id, name").eq("active", True).execute().data

def _brand_matches(clean_item: str, product_name: str) -> bool:
    query_signal = _product_signal_text(clean_item)
    if not query_signal:
        return True
    
    product_family = _product_family(product_name)
    query_variants = _spelling_variants(query_signal)
    
    best_brand_score = 0.0
    for q_var in query_variants:
        score = fuzz.WRatio(q_var, product_family)
        best_brand_score = max(best_brand_score, score)
        
    return best_brand_score >= 65.0

test_cases = [
    "Quiero sprite de 2L",
    "sielo 2.5l",
    "2 de 2l",
    "coca 2l",
    "oro 2l",
    "quiero 2 big colas",
    "cifru 1l",
    "volt",
    "vol de 300ml"
]

print("=== BRAND MATCHING TEST (NO SPLIT) ===")
for test_input in test_cases:
    clean_item = _clean_segment(test_input)
    query_signal = _product_signal_text(clean_item)
    print(f"\nInput: '{test_input}' -> Clean: '{clean_item}' -> Signal: '{query_signal}'")
    matches = []
    for p in products:
        if _brand_matches(clean_item, p["name"]):
            matches.append(p["name"])
    print(f"Allowed products ({len(matches)}): {matches}")
