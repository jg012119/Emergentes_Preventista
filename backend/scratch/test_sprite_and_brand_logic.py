import sys
from pathlib import Path
from typing import Any

sys.path.append(str(Path("/home/jairomgr/Proyectos/expo/Emergentes_Preventista/backend")))

from app.config import get_supabase_admin
from app.routes.nlp import (
    _clean_segment,
    _product_signal_text,
    _spelling_variants,
    _product_aliases,
    _score_alias,
    _canonical_presentation,
    NLPSkuCandidate
)
from rapidfuzz import fuzz

db = get_supabase_admin()
products = db.table("products").select("*").eq("active", True).execute().data
aliases = db.table("product_aliases").select("*").eq("is_active", True).execute().data

def _brand_matches(clean_item: str, product: dict[str, Any], aliases: list[dict[str, Any]]) -> bool:
    query_signal = _product_signal_text(clean_item)
    if not query_signal:
        return True
    
    product_brand = _product_signal_text(product.get("name"))
    query_variants = _spelling_variants(query_signal)
    
    best_brand_score = 0.0
    for q_var in query_variants:
        score = fuzz.WRatio(q_var, product_brand)
        best_brand_score = max(best_brand_score, score)
        
    if best_brand_score >= 65.0:
        return True
        
    # Check aliases
    for alias_obj in _product_aliases(product, aliases):
        alias_text = alias_obj["alias"]
        alias_brand = _product_signal_text(alias_text)
        for q_var in query_variants:
            score = fuzz.WRatio(q_var, alias_brand)
            if score >= 65.0:
                return True
                
    return False

def _sku_candidates_modified(clean_item: str, products: list[dict[str, Any]], aliases: list[dict[str, Any]]) -> list[NLPSkuCandidate]:
    candidates: dict[str, NLPSkuCandidate] = {}

    for product in products:
        if not _brand_matches(clean_item, product, aliases):
            continue

        best_score = 0.0
        for alias in _product_aliases(product, aliases):
            best_score = max(best_score, _score_alias(clean_item, alias["alias"], alias["weight"]))

        if best_score < 45:
            continue

        product_id = product.get("id")
        candidates[str(product_id)] = NLPSkuCandidate(
            sku_id=product_id,
            product_id=product_id,
            product=product.get("name"),
            presentation=_canonical_presentation(product.get("name")),
            score=round(best_score / 100, 2),
            stock=int(product.get("stock") or 0),
            price=float(product.get("price") or 0),
        )

    return sorted(candidates.values(), key=lambda item: item.score, reverse=True)[:4]

test_queries = [
    "Quiero sprite de 2L",
    "coca 2l",
    "sielo 2.5l",
    "oro 2l",
    "2 de 2l",
    "quiero 2 big colas",
    "volt 300ml"
]

print("=== CANDIDATES TEST WITH BRAND SIGNAL MATCHES ===")
for q in test_queries:
    clean = _clean_segment(q)
    cands = _sku_candidates_modified(clean, products, aliases)
    print(f"\nQuery: '{q}' -> Clean: '{clean}'")
    if not cands:
        print("  No candidates found")
    for c in cands:
        print(f"  Candidate: {c.product:<20} | Score: {c.score:.2f}")
