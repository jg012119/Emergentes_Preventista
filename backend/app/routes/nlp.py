"""Natural language parsing for voice and chat orders."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from dateparser.search import search_dates
from fastapi import APIRouter, Depends
from rapidfuzz import fuzz

from app.config import get_supabase_admin
from app.models.schemas import NLPParseRequest, NLPParseResponse, NLPProductMatch
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/nlp", tags=["nlp"])

QUANTITY_WORDS = {
    "un": 1,
    "una": 1,
    "uno": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
    "once": 11,
    "doce": 12,
    "docena": 12,
}

FILLER_RE = re.compile(
    r"^(quiero|necesito|dame|manda|mandame|agrega|agregar|pedir|pedido|por favor|me das|ponme|seria)\s+",
    re.IGNORECASE,
)
SPLIT_RE = re.compile(r"\s*(?:,|;|\+|\by\b|\btambien\b|\badicionalmente\b|\bmas\b)\s+")


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = text.replace("-", " ")
    text = re.sub(r"[^a-z0-9.]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _unit_variants(value: str) -> set[str]:
    variants = {_normalize(value)}
    queue = list(variants)
    for item in queue:
        generated = {
            re.sub(r"(\d+(?:\.\d+)?)\s*l\b", r"\1l", item),
            re.sub(r"(\d+(?:\.\d+)?)l\b", r"\1 litros", item),
            re.sub(r"(\d+(?:\.\d+)?)\s*litros?\b", r"\1l", item),
            re.sub(r"(\d+)\s*ml\b", r"\1ml", item),
            re.sub(r"(\d+)ml\b", r"\1 ml", item),
            re.sub(r"(\d+)\s*mililitros?\b", r"\1ml", item),
        }
        variants.update(_normalize(g) for g in generated if g)
    return {v for v in variants if v}


def _product_aliases(product: dict[str, Any]) -> list[str]:
    name = product.get("name", "")
    aliases = set(_unit_variants(name))
    aliases.add(_normalize(re.sub(r"\bcola\b", "", name)))
    aliases.add(_normalize(re.sub(r"\bcoca cola\b", "coca", name, flags=re.IGNORECASE)))
    return [alias for alias in aliases if alias]


def _clean_segment(segment: str) -> str:
    clean = _normalize(segment)
    previous = None
    while clean and clean != previous:
        previous = clean
        clean = FILLER_RE.sub("", clean).strip()
    return clean


def _parse_quantity(segment: str) -> int:
    clean = _clean_segment(segment)
    if not clean:
        return 1

    match = re.search(r"\bx\s*(\d{1,3})\b", clean)
    if match:
        return max(1, int(match.group(1)))

    match = re.match(r"(\d{1,3})\b", clean)
    if match:
        return max(1, int(match.group(1)))

    tokens = clean.split()[:4]
    for token in tokens:
        if token in QUANTITY_WORDS:
            return QUANTITY_WORDS[token]
    return 1


def _best_product(segment: str, products: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, int]:
    segment_variants = _unit_variants(segment)
    best_product = None
    best_score = 0

    for product in products:
        aliases = _product_aliases(product)
        score = 0
        for segment_variant in segment_variants:
            for alias in aliases:
                score = max(score, fuzz.WRatio(segment_variant, alias), fuzz.token_set_ratio(segment_variant, alias))
        if score > best_score:
            best_product = product
            best_score = score

    if best_score < 64:
        return None, best_score
    return best_product, best_score


def _extract_delivery_date(text: str) -> str | None:
    try:
        results = search_dates(
            text,
            languages=["es"],
            settings={"PREFER_DATES_FROM": "future", "DATE_ORDER": "DMY"},
        )
    except Exception:
        return None

    if not results:
        return None

    for raw, parsed in results:
        if re.search(r"\b(entrega|entregar|manana|hoy|lunes|martes|miercoles|jueves|viernes|sabado|domingo)\b", _normalize(raw)):
            return parsed.date().isoformat()
    return results[0][1].date().isoformat()


@router.post("/parse", response_model=NLPParseResponse)
async def parse_order_text(body: NLPParseRequest, _user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    text = (body.text or "").strip()

    products = db.table("products").select("*").eq("active", True).execute().data or []
    segments = [part for part in SPLIT_RE.split(_normalize(text)) if part]
    if not segments and text:
        segments = [_normalize(text)]

    matches: dict[str, NLPProductMatch] = {}
    for segment in segments:
        product, _score = _best_product(segment, products)
        if not product:
            continue

        quantity = _parse_quantity(segment)
        product_id = product.get("id")
        price = float(product.get("price") or 0)
        subtotal = price * quantity

        key = str(product_id or product.get("name"))
        if key in matches:
            current = matches[key]
            current.quantity += quantity
            current.subtotal += subtotal
        else:
            matches[key] = NLPProductMatch(
                name=product.get("name", "Producto"),
                product_id=product_id,
                quantity=quantity,
                unit_price=price,
                subtotal=subtotal,
            )

    parsed_products = list(matches.values())
    total = sum(item.subtotal for item in parsed_products)
    delivery_date = _extract_delivery_date(text)

    if not parsed_products:
        message = (
            "No pude identificar productos en el audio. Intenta decir cantidad y producto, "
            "por ejemplo: dos Big Cola 3 litros y un Sporade 500 ml."
        )
    else:
        product_lines = ", ".join(f"{item.quantity} x {item.name}" for item in parsed_products)
        delivery_copy = f" Entrega sugerida: {delivery_date}." if delivery_date else ""
        message = (
            f"Interprete: {product_lines}. Total estimado: Bs {total:.2f}."
            f"{delivery_copy} Revisa el pedido antes de confirmarlo."
        )

    return NLPParseResponse(
        products=parsed_products,
        delivery_date=delivery_date,
        total=total,
        requires_confirmation=True,
        message=message,
    )
