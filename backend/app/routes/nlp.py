"""Natural language parsing for voice and chat orders."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from dateparser.search import search_dates
from fastapi import APIRouter, Depends
from rapidfuzz import fuzz

from ..config import get_supabase_admin
from ..models.schemas import NLPParseRequest, NLPParseResponse, NLPProductMatch
from ..utils.auth import get_current_user_id

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
    "una docena": 12,
    "trece": 13,
    "catorce": 14,
    "quince": 15,
    "dieciseis": 16,
    "diecisiete": 17,
    "dieciocho": 18,
    "diecinueve": 19,
    "veinte": 20,
    "veintiuno": 21,
    "veintidos": 22,
    "veintitres": 23,
    "veinticuatro": 24,
    "veinticinco": 25,
    "treinta": 30,
    "cuarenta": 40,
    "cincuenta": 50,
    "media docena": 6,
}

# Aliases for text-based sizes (normalized form -> canonical ml/l form)
SIZE_ALIASES = {
    "medio litro": "500ml",
    "medio": "500ml",
    "litro y medio": "1.5l",
    "cuarto de litro": "250ml",
    "cuarto": "250ml",
    "de litro": "1l",
    "litro": "1l",
    "mediano": "500ml",
    "medianos": "500ml",
    "familiar": "2.5l",
    "familiares": "2.5l",
    "personal": "330ml",
    "personales": "330ml",
    "grande": "2.5l",
    "grandes": "2.5l",
    "chico": "300ml",
    "chicos": "300ml",
    "pequeño": "300ml",
    "pequeños": "300ml",
    "300": "300ml",
    "500": "500ml",
    "600": "600ml",
    "750": "750ml",
    "330": "330ml",
    "250": "250ml",
    "400": "400ml",
    "450": "450ml",
    "1.5": "1.5l",
    "2.5": "2.5l",
    "3.3": "3.3l",
    "2.25": "2.25l",
}

ORTHO_MAP = {
    "biq cola": "big cola",
    "bigc cola": "big cola",
    "volt 300": "volt 300ml",
    "volt 500ml": "volt 500ml",
    "litruz": "litros",
    "litrs": "litros",
    "lt": "l",
    "aguas": "agua",
    "agua": "agua",
    "agua": "agua",
    "aguas": "agua",
    "aguas": "agua",
    "agua": "agua",
}

FILLER_RE = re.compile(
    r"^(quiero|necesito|dame|manda|mandame|agrega|agregar|pedir|pedido|por favor|me das|ponme|seria|casero|caserita|anotame|dejame|para mi tiendita|para mi tienda|para el almacen|tiendita|tienda|almacen|porfa|porfis|hola|buen dia|buenas tardes|buenas noches)\s+",
    re.IGNORECASE,
)
SPLIT_RE = re.compile(
    r"\s*(?:,|;|\+|\by\b|\btambien\b|\badicionalmente\b|\bmas\b|\bdespues\b|\bluego\b|\baparte\b|\bjunto\s+con\b|\bcon\b)\s+"
)


def _apply_ortho(text: str) -> str:
    """Replace known misspellings with correct tokens."""
    for wrong, right in ORTHO_MAP.items():
        pattern = re.compile(rf"\b{re.escape(wrong)}\b", re.IGNORECASE)
        text = pattern.sub(right, text)
    return text


def _normalize(value: str) -> str:
    # First apply orthographic fixes
    text = _apply_ortho(value or "")
    text = unicodedata.normalize("NFKD", text)
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
        # Add text-based size aliases (medio litro -> 500ml, etc.)
        for alias, canonical in SIZE_ALIASES.items():
            if alias in item:
                generated.add(item.replace(alias, canonical))
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

    # Sort multi-word quantities first
    sorted_quants = sorted(QUANTITY_WORDS.items(), key=lambda x: len(x[0].split()), reverse=True)
    
    # Try exact phrase matches first
    for phrase, val in sorted_quants:
        if re.search(rf"\b{phrase}\b", clean):
            return val

    # Try token based matching for robust fallbacks
    tokens = clean.split()[:4]
    for token in tokens:
        if token in QUANTITY_WORDS:
            return QUANTITY_WORDS[token]
    return 1


# Words that indicate date/time context — should be stripped before product matching
_DATE_FILLER_RE = re.compile(
    r"\b(para|manana|mañana|hoy|ayer|lunes|martes|miercoles|jueves|viernes|sabado|domingo"
    r"|enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre"
    r"|esta semana|la semana|proximo|proxima|siguiente|despues|luego|tarde|noche|dia)\b",
    re.IGNORECASE,
)

# Pattern that matches segments which are ONLY size/volume info (no product name)
_ONLY_SIZE_RE = re.compile(
    r"^[\d\s.,xX]*(ml|l|lt|lts|litros?|litruz|litrs)?$",
    re.IGNORECASE,
)


def _best_product(segment: str, products: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, int]:
    # Strip quantities from segment so "2 volt" doesn't match "2L"
    clean_seg = _clean_segment(segment)

    # Remove date/time filler words so "para mañana" doesn't pollute matching
    if clean_seg:
        clean_seg = _DATE_FILLER_RE.sub("", clean_seg)
        clean_seg = re.sub(r"\s+", " ", clean_seg).strip()

    if clean_seg:
        sorted_quants = sorted(QUANTITY_WORDS.keys(), key=lambda x: len(x.split()), reverse=True)
        for q in sorted_quants:
            clean_seg = re.sub(rf"\b{q}\b", "", clean_seg, flags=re.IGNORECASE)
        # Remove standalone numbers that are NOT attached to ml/l
        clean_seg = re.sub(r"\b\d+(?:\.\d+)?\b(?!\s*(?:ml|l|litros?))", "", clean_seg, flags=re.IGNORECASE)
        clean_seg = re.sub(r"\s+", " ", clean_seg).strip()

    # ⛔ Guard: if what remains is ONLY a size token (e.g. "1l", "500ml"),
    # there is no product name to match — skip to avoid false positives.
    if not clean_seg or _ONLY_SIZE_RE.fullmatch(clean_seg):
        return None, 0

    segment_variants = _unit_variants(clean_seg or segment)
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

    # Fallback: if nothing found or low confidence, do a broad fuzzy match
    if not best_product or best_score < 70:
        for product in products:
            name = product.get("name", "")
            cleaned_seg = re.sub(r"\b\d+(?:\.\d+)?\s*(ml|l|lt|lts|litros?|litruz|litrs)\b", "", segment, flags=re.IGNORECASE)
            cleaned_seg = _DATE_FILLER_RE.sub("", cleaned_seg).strip()
            if not cleaned_seg or _ONLY_SIZE_RE.fullmatch(cleaned_seg.strip()):
                continue
            ratio = fuzz.ratio(cleaned_seg.lower(), name.lower())
            if ratio > best_score:
                best_product = product
                best_score = ratio

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
