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
    """Exact case‑insensitive match for a product name.
    Returns the matching product dict (id, name) or None if not found."""
    for product in products:
        if product["name"].lower() == name.lower():
            return product
    return None

def extract_quantities(doc) -> List[Dict[str, Any]]:
    """Extract quantity‑product pairs from a spaCy doc.
    Handles patterns like "2 L Coca Cola", "2L Coca Cola" and also
    cases where the quantity appears before the product name or stands
    alone (e.g., user says "2" then later mentions "Coca Cola").
    The function will:
      * Return items with both name and quantity when both are detected.
      * Keep a pending quantity if no product token follows.
      * When a later product token appears, associate the pending quantity
        with that product (contextual linking).
    The caller (`parse_order`) will generate a clarification question if
    a quantity remains without a product.
    """
    items: List[Dict[str, Any]] = []
    pending_qty: Optional[int] = None
    last_product_name: Optional[str] = None
    i = 0
    while i < len(doc):
        token = doc[i]
        # Direct "2L" token (e.g., "2L", "3L")
        if token.text.lower().endswith('l') and token.text[:-1].isdigit():
            qty = int(token.text[:-1])
                nxt = doc[nxt.i + 1] if nxt.i + 1 < len(doc) else None
            if product_tokens:
                items.append({"name": " ".join(product_tokens), "quantity": qty})
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
            # Fallback: try to find a product that contains the generic name and a size that matches the quantity
            qty = item["quantity"]
            size_variants = [f"{qty}L", f"{qty} L", f"{qty}ml", f"{qty} ml"]
            possible = [p for p in products if item["name"].lower() in p["name"].lower()]
            for p in possible:
                if any(variant.lower() in p["name"].lower() for variant in size_variants):
                    match = p
                    break
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
