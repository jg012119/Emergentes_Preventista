import sys
from pathlib import Path

sys.path.append(str(Path("/home/jairomgr/Proyectos/expo/Emergentes_Preventista/backend")))

from app.config import get_supabase_admin
from app.routes.nlp import _clean_segment, _sku_candidates, _fetch_aliases

db = get_supabase_admin()
products = db.table("products").select("*").eq("active", True).execute().data
aliases = _fetch_aliases(db)

test_queries = [
    "Quiero sprite de 2L",
    "coca 2l",
    "oro 2l",
    "2 de 2l"
]

print("=== LIVE NLP BRAND MATCHING TEST ===")
for q in test_queries:
    clean = _clean_segment(q)
    cands = _sku_candidates(clean, products, aliases)
    print(f"Query: '{q}' -> Clean: '{clean}'")
    if not cands:
        print("  No candidates found")
    for c in cands:
        print(f"  Candidate: {c.product:<20} | Score: {c.score:.2f}")
