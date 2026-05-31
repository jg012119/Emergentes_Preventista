import json
from datetime import datetime, date
from typing import List, Dict, Any, Optional

import spacy
from rapidfuzz import process, fuzz
import dateparser

# Load spaCy Spanish model (download if missing)
def load_spacy_model():
    try:
        return spacy.load("es_core_news_md")
    except OSError:
        # Model not installed – install it programmatically
        import subprocess, sys
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "es_core_news_md"])
        return spacy.load("es_core_news_md")

nlp = load_spacy_model()

def fetch_active_products(db) -> List[Dict[str, Any]]:
    """Return a list of active products with their id and name.
    """
    result = db.table("products").select("id, name").eq("active", True).execute()
    return result.data

def match_product(name: str, products: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Find the best fuzzy match for a product name.
    Returns the matching product dict (id, name) and confidence score.
    """
    choices = {p["name"]: p for p in products}
    match, score, _ = process.extractOne(
        name,
        list(choices.keys()),
        scorer=fuzz.WRatio,
    )
    if score < 70:  # threshold for acceptable match
        return None
    product = choices[match]
    product["match_score"] = score
    return product

def extract_quantities(doc) -> List[Dict[str, Any]]:
    """Extract quantity‑product pairs from a spaCy doc.
    Returns a list of dicts: {"name": str, "quantity": int}
    """
    items = []
    # Simple heuristic: look for a numeral followed by a noun (product)
    for token in doc:
        if token.like_num:
            # Capture the number (int) and the next token that is a noun or proper noun
            qty = int(token.text)
            # Look ahead for the product name (could be multiple tokens)
            product_tokens = []
            nxt = token.nbor(1) if token.i + 1 < len(doc) else None
            while nxt and nxt.pos_ in {"NOUN", "PROPN", "ADJ"}:
                product_tokens.append(nxt.text)
                if nxt.i + 1 < len(doc):
                    nxt = doc[nxt.i + 1]
                else:
                    break
            if product_tokens:
                product_name = " ".join(product_tokens)
                items.append({"name": product_name, "quantity": qty})
    return items

def extract_date(text: str) -> Optional[date]:
    """Parse a Spanish date expression using dateparser.
    Returns a date object or None.
    """
    dt = dateparser.parse(text, languages=["es"], settings={"RETURN_AS_TIMEZONE_AWARE": False})
    if dt:
        return dt.date()
    return None

def parse_order(text: str, db) -> Dict[str, Any]:
    """Parse free‑text order into a draft payload.
    Returns a dict with keys:
        - order: dict compatible with OrderDraftRequest
        - nlp_data: raw extraction details
        - questions: list of follow‑up prompts when data is missing or ambiguous
    """
    doc = nlp(text)
    products = fetch_active_products(db)

    extracted_items = extract_quantities(doc)
    order_items = []
    questions = []
    nlp_data = {
        "entities": [],
        "matches": [],
        "date": None,
    }

    # Process each extracted item
    for item in extracted_items:
        match = match_product(item["name"], products)
        if not match:
            questions.append({
                "type": "product",
                "message": f"No se encontró el producto '{item['name']}'. ¿Podrías especificar el nombre exacto?",
                "original": item["name"]
            })
            continue
        order_items.append({
            "product_id": match["id"],
            "quantity": item["quantity"]
        })
        nlp_data["matches"].append({
            "input": item["name"],
            "matched": match["name"],
            "score": match.get("match_score", 0)
        })

    # Try to extract a delivery date
    parsed_date = extract_date(text)
    if parsed_date:
        nlp_data["date"] = parsed_date.isoformat()
    else:
        # If a date is required but not found, ask the user
        questions.append({
            "type": "date",
            "message": "¿Cuál es la fecha de entrega deseada? (por ejemplo, 'mañana a las 10')"
        })

    # Build the order draft structure
    order = {
        "store_id": None,  # store must be supplied by client or later question
        "delivery_date": parsed_date.isoformat() if parsed_date else None,
        "notes": None,
        "items": order_items,
    }

    return {
        "order": order,
        "nlp_data": nlp_data,
        "questions": questions or None,
    }
