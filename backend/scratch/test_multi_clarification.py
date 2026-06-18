import sys
from pathlib import Path

sys.path.append(str(Path("/home/jairomgr/Proyectos/expo/Emergentes_Preventista/backend")))

from app.config import get_supabase_admin
from app.routes.nlp import (
    _normalize,
    _remove_quantity,
    _parse_quantity,
    _split_order_segments,
    _get_brand_keywords,
    NO_PRODUCT_SIGNAL_TOKENS,
    FILLER_RE
)

db = get_supabase_admin()

def _get_pending_product_name(pending: dict) -> str | None:
    text = pending.get("question_text", "")
    if pending.get("question_type") == "quantity":
        if "de " in text:
            prod = text.split("de ")[-1].replace("?", "").strip()
            return prod
    elif pending.get("question_type") in ("presentation", "sku", "product"):
        options = pending.get("options") or []
        if options:
            return options[0].get("product") or options[0].get("name")
        if "de " in text:
            prod = text.split("de ")[-1].replace("?", "").strip()
            if ":" in prod:
                prod = prod.split(":")[0].strip()
            return prod
    return None

def _clarification_matches_segment(pending: dict, segment: str) -> bool:
    prod_name = _get_pending_product_name(pending)
    if not prod_name:
        return False
    
    brand1 = _get_brand_keywords(prod_name)
    brand2 = _get_brand_keywords(segment)
    if brand1 and brand2:
        if brand1 & brand2:
            return True
            
    norm1 = _normalize(prod_name)
    norm2 = _normalize(segment)
    clean2 = _remove_quantity(norm2)
    
    words1 = set(norm1.split())
    words2 = set(clean2.split())
    significant_words1 = {w for w in words1 if len(w) >= 3 and w not in NO_PRODUCT_SIGNAL_TOKENS}
    significant_words2 = {w for w in words2 if len(w) >= 3 and w not in NO_PRODUCT_SIGNAL_TOKENS}
    if significant_words1 & significant_words2:
        return True
        
    return False

# Mock pending clarifications
pendings = [
    {
        "id": "event_1",
        "question_type": "quantity",
        "question_text": "¿Cuantas unidades quieres de Volt 300ml?",
    },
    {
        "id": "event_2",
        "question_type": "quantity",
        "question_text": "¿Cuantas unidades quieres de Agua Cielo 500ml?",
    },
    {
        "id": "event_3",
        "question_type": "quantity",
        "question_text": "¿Cuantas unidades quieres de Coca-Cola 2L?",
    }
]

user_reply = "Volt 5, agua 7 y 1 coca cola"
print(f"User reply: '{user_reply}'")

segments = _split_order_segments(user_reply)
print("Segments:", segments)

resolved_parts = []
matched_ids = []

for segment in segments:
    # Find matching pending clarification
    matched_pending = None
    for pending in pendings:
        if pending["id"] in matched_ids:
            continue
        if _clarification_matches_segment(pending, segment):
            matched_pending = pending
            break
            
    if matched_pending:
        matched_ids.append(matched_pending["id"])
        qty = _parse_quantity(segment)
        prod_name = _get_pending_product_name(matched_pending)
        resolved_parts.append(f"{qty} {prod_name}")
        print(f"Segment '{segment}' matched pending '{matched_pending['question_text']}' -> Resolved to '{qty} {prod_name}'")
    else:
        print(f"Segment '{segment}' did not match any pending clarification")

if resolved_parts:
    enriched_text = " y ".join(resolved_parts)
    print("Enriched text:", enriched_text)
