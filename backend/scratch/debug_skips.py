import sys
from pathlib import Path

sys.path.append(str(Path("/home/jairomgr/Proyectos/expo/Emergentes_Preventista/backend")))

from app.routes.nlp import (
    NO_PRODUCT_SIGNAL_TOKENS,
    _normalize,
    _remove_quantity,
    _has_product_signal,
    _product_signal_text,
    _split_order_segments,
    _strip_date_clause,
    FILLER_RE,
    _quantity_info
)
from app.config import get_supabase_admin

import re

def _item_fragment_new(segment: str) -> str:
    from app.routes.nlp import _quantity_info, FILLER_RE, NO_PRODUCT_SIGNAL_TOKENS
    info = _quantity_info(segment)
    if info:
        _, start, _end = info
        tokens = segment.split()
        has_non_filler = False
        for token in tokens[:start]:
            normalized_token = token.lower().strip(".,!?()-\"'/")
            if not FILLER_RE.match(normalized_token) and normalized_token not in NO_PRODUCT_SIGNAL_TOKENS:
                has_non_filler = True
                break
        if not has_non_filler:
            return " ".join(tokens[start:])
    return segment

print("volt in NO_PRODUCT_SIGNAL_TOKENS:", "volt" in NO_PRODUCT_SIGNAL_TOKENS)
print("agua in NO_PRODUCT_SIGNAL_TOKENS:", "agua" in NO_PRODUCT_SIGNAL_TOKENS)

# Debug Coca-Cola 2L matching
from app.routes.nlp import _parse_order_payload, _sku_candidates
print("\n--- Debugging Coca-Cola 2L ---")
db = get_supabase_admin()
products = db.table("products").select("*").eq("active", True).execute().data
aliases = db.table("product_aliases").select("*").eq("is_active", True).execute().data
cands = _sku_candidates("coca de 2 litros", products, aliases)
print("Candidates for 'coca de 2 litros':")
for c in cands:
    print(f"  {c.product} ({c.presentation}) score: {c.score}")

# Test parsing of enriched text
parsed = _parse_order_payload(db, text="1 Coca-Cola 2L y 1 Volt 300ml", user_id="5eb64f36-6fdf-47bb-91b6-b6b8ce471a24", persist=False)
print("Requires clarification:", parsed.requires_clarification)
for item in parsed.items:
    print(f"Parsed Item: {item.raw_text} | Normal: {item.producto_normalizado} | Qty: {item.cantidad} | SKU: {item.sku_id}")
    for c in item.sku_candidates:
        print(f"    Candidate: {c.product} ({c.presentation}) score: {c.score}")



