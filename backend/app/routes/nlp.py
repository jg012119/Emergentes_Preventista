"""Natural language parsing for voice and chat orders."""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, timedelta, timezone
from typing import Any

from dateparser.search import search_dates
from fastapi import APIRouter, Depends, HTTPException, Query, status
from rapidfuzz import fuzz

from app.config import get_supabase_admin
from app.models.schemas import (
    NLPCorrectionRequest,
    NLPClarificationQuestion,
    NLPDraftOrderResponse,
    NLPParsedOrderItem,
    NLPParseOrderRequest,
    NLPParseOrderResponse,
    NLPParseRequest,
    NLPParseResponse,
    NLPProductMatch,
    NLPSkuCandidate,
    NLPValidateExtractionRequest,
    NLPValidationIssue,
    NLPValidationResponse,
    OrderItemOut,
    OrderOut,
)
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/nlp", tags=["nlp"])

SOLID_KEYWORDS = {
    "papas", "papitas", "papas fritas", "nachos", "galletas", "dulce", "hamburguesa",
    "pizza", "sandwich", "bocadillo", "comida", "alimento", "snack", "papas chips"
}
ALCOHOL_KEYWORDS = {
    "cheba", "cerveza", "birra", "chela", "vino", "whisky", "ron", "vodka", "licor"
}

AUTO_ACCEPT_SCORE = 90
CONFIRM_SCORE = 70
AMBIGUOUS_GAP = 5
CHAT_ACTION_PREFIX = "@@action "
MAX_CLARIFICATION_AGE_SECONDS = 180
CONTEXTUAL_REPLY_RE = re.compile(
    r"^\s*(si|sí|ya|ok|okay|dale|correcto|eso|esa|ese|tambien|también|ademas|además|y|sumale|agrega|agregale|agregame|para|pa|tienda|cliente)\b",
    re.IGNORECASE,
)
CONTEXT_APPEND_RE = re.compile(
    r"^\s*(tambien|también|ademas|además|y|sumale|agrega|agregale|agregame)\b",
    re.IGNORECASE,
)
# Negation patterns: "no quiero X, solo Y", "sin X", "mejor solo Y"
NEGATION_RE = re.compile(
    r"^\s*(?:no\s+(?:quiero|me\s+pongas|pongas|mandes?|quiero|necesito)|sin\s+|mejor\s+(?:solo|sin)\s+|solo\s+)",
    re.IGNORECASE,
)
NEGATION_PREFIX_RE = re.compile(
    r"^\s*(?:no\s+(?:quiero|me\s+pongas|pongas|mandes?)|sin\s+(?:coca|cola|agua|volt|big|cielo|pulp|cifrut)\b)",
    re.IGNORECASE,
)
SOLO_PATTERN_RE = re.compile(
    r"\bsolo\s+(.+?)(?:\s*(?:porf(?:avor)?|please|por\s+favor|gracias))?\s*$",
    re.IGNORECASE,
)
COMMAND_TEXTS = {"menu", "catalogo", "productos", "lista", "lista de pedidos", "estado"}
GREETING_TEXTS = {
    "hola",
    "buenas",
    "buenos dias",
    "buen dia",
    "buenas tardes",
    "gracias",
    "ok",
    "okay",
}

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
    r"^(quiero|necesito|dame|manda|mandame|mandale|agrega|agregame|agregar|pedir|pedido|por favor|me das|me manda|ponme|seria|anotame|pasame|dejame|llevame|despachame|ehhh|ehh|eh|este|a ver|entonces|bueno|buena|oye|nomas|eso nomas|después|despues|hola buenas|hola|buenas)\b\s*",
    re.IGNORECASE,
)
ORDER_INTENT_RE = re.compile(
    r"\b(quiero|necesito|dame|manda|mandame|mandale|agrega|agregame|anotame|pasame|dejame|llevame|despachame|pedido|orden|para|pa)\b",
    re.IGNORECASE,
)
SPLIT_RE = re.compile(r"\s*(?:,|;|\+|\by\b|\btambien\b|\badicionalmente\b|\bmas\b)\s+")
DATE_KEYWORD_RE = re.compile(
    r"\b(entrega|entregar|fecha|para|pa|hoy|pasado|manana|mañana|ayer|lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)\b",
    re.IGNORECASE,
)
DATE_TRAILING_RE = re.compile(
    r"\s+\b(?:para|pa)\s+(hoy|pasado\s+manana|pasado\s+mañana|manana|mañana|el\s+)?(lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo|hoy|manana|mañana)\b\s*\.?$",
    re.IGNORECASE,
)
PRESENTATION_RE = re.compile(r"\b(\d+(?:[\.,]\d+)?)\s*(ml|l|lt|lts|litro|litros|mililitro|mililitros)\b", re.IGNORECASE)
UNIT_RE = re.compile(r"\b(caja|cajas|cajita|cajitas|lata|latas|six|sixpack|six pack|pack|packs|paquete|paquetes)\b", re.IGNORECASE)
PRESENTATION_UNIT_TOKENS = {
    "ml",
    "l",
    "lt",
    "lts",
    "litro",
    "litros",
    "litrso",
    "litors",
    "litroos",
    "mililitro",
    "mililitros",
}
COMMERCIAL_UNIT_TOKENS = {
    "caja",
    "cajas",
    "cajita",
    "cajitas",
    "lata",
    "latas",
    "six",
    "sixpack",
    "pack",
    "packs",
    "paquete",
    "paquetes",
}
NO_PRODUCT_SIGNAL_TOKENS = {
    "a",
    "mi",
    "y",
    "en",
    "con",
    "por",
    "su",
    "tu",
    "o",
    "de",
    "del",
    "la",
    "el",
    "las",
    "los",
    "un",
    "una",
    "uno",
    "dos",
    "tres",
    "cuatro",
    "cinco",
    "seis",
    "siete",
    "ocho",
    "nueve",
    "diez",
    "once",
    "doce",
    "docena",
    "chica",
    "chico",
    "chika",
    "chiko",
    "chiquita",
    "chiquito",
    "chikita",
    "chikito",
    "grande",
    "grand",
    "familiar",
    "personal",
    "producto",
    "productos",
    "pedido",
    "pedidos",
    "litro",
    "litros",
    "ml",
    "l",
    "lt",
    "lts",
    "hoy",
    "manana",
    "mañana",
    "pasado",
    "ayer",
    "lunes",
    "martes",
    "miercoles",
    "miércoles",
    "jueves",
    "viernes",
    "sabado",
    "sábado",
    "domingo",
    "fecha",
    "entrega",
    "entregar",
    "para",
    "pa",
    "tienda",
    "cliente",
    "don",
    "dona",
    "doña",
    "quiero",
    "necesito",
    "dame",
    "manda",
    "mandame",
    "mandale",
    "agrega",
    "agregame",
    "anotame",
    "pasame",
    "dejame",
    "llevame",
    "despachame",
    "porfavor",
    "favor",
    "gracias",
}
TYPO_REPLACEMENTS = (
    (r"\bchika\b", "chica"),
    (r"\bchiko\b", "chico"),
    (r"\bchikita\b", "chiquita"),
    (r"\bchikito\b", "chiquito"),
    (r"\bgrnade\b", "grande"),
    (r"\bgrand\b", "grande"),
    (r"\bmaniana\b", "manana"),
    (r"\blitrso\b", "litros"),
    (r"\blitors\b", "litros"),
    (r"\blitroos\b", "litros"),
    (r"\bsielo\b", "cielo"),
    (r"\bsiello\b", "cielo"),
    (r"\bcieelo\b", "cielo"),
    (r"\bcieloo\b", "cielo"),
    (r"\bcifru\b", "cifrut"),
    (r"\bcifruth\b", "cifrut"),
    (r"\bvotl\b", "volt"),
    (r"\bvol\b", "volt"),
    (r"\bbolt\b", "volt"),
    (r"\bbol\b", "volt"),
    (r"\bpulpp\b", "pulp"),
    (r"\bbik\b", "big"),
    (r"\bbigg\b", "big"),
    # ASR-typical errors
    (r"\bcocacola\b", "coca cola"),
    (r"\bbigcola\b", "big cola"),
    (r"\baguacielo\b", "agua cielo"),
    (r"\bfreetea\b", "free tea"),
    (r"\besporate\b", "sporade"),
    (r"\besporade\b", "sporade"),
    (r"\bsporad\b", "sporade"),
    (r"\bcoquita\b", "coca cola"),
    (r"\bcoquitas\b", "coca cola"),
)


def _normalize(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("-", " ")
    text = re.sub(r"[^a-z0-9.]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _unit_variants(value: str | None) -> set[str]:
    variants = {_normalize(value)}
    queue = list(variants)
    for item in queue:
        generated = {
            re.sub(r"(\d+(?:\.\d+)?)\s*l\b", r"\1l", item),
            re.sub(r"(\d+(?:\.\d+)?)l\b", r"\1 litros", item),
            re.sub(r"(\d+(?:\.\d+)?)\s*litros?\b", r"\1l", item),
            re.sub(r"(\d+(?:\.\d+)?)\s*lt?s?\b", r"\1l", item),
            re.sub(r"(\d+)\s*ml\b", r"\1ml", item),
            re.sub(r"(\d+)ml\b", r"\1 ml", item),
            re.sub(r"(\d+)\s*mililitros?\b", r"\1ml", item),
            # Strip units completely as a matching option (e.g. "500ml" -> "500")
            re.sub(r"(\d+(?:\.\d+)?)\s*(?:ml|l|lt|lts|litros?|mililitros?)\b", r"\1", item),
        }
        variants.update(_normalize(g) for g in generated if g)
    return {v for v in variants if v}


def _spelling_variants(value: str | None) -> set[str]:
    base = _normalize(value)
    if not base:
        return set()

    variants = {base, re.sub(r"([a-z])\1{1,}", r"\1", base)}
    for pattern, replacement in TYPO_REPLACEMENTS:
        for variant in list(variants):
            variants.add(re.sub(pattern, replacement, variant))

    for variant in list(variants):
        if "k" in variant:
            variants.add(variant.replace("k", "c"))
            variants.add(variant.replace("ki", "qui").replace("ke", "que"))

    # Plural to singular spelling variants (e.g. "aguas" -> "agua", "colas" -> "cola")
    for variant in list(variants):
        words = variant.split()
        changed = False
        new_words = []
        for w in words:
            if w.endswith("s") and len(w) >= 4 and not w.endswith("lts"):
                new_words.append(w[:-1])
                changed = True
            else:
                new_words.append(w)
        if changed:
            variants.add(" ".join(new_words))

    return {variant for variant in variants if variant}


def _match_variants(value: str | None) -> set[str]:
    variants: set[str] = set()
    for spelling_variant in _spelling_variants(value):
        variants.update(_unit_variants(spelling_variant))
    return variants


def _canonical_presentation(value: str | None) -> str | None:
    normalized = _normalize(value)
    for pattern, replacement in TYPO_REPLACEMENTS:
        normalized = re.sub(pattern, replacement, normalized)

    match = PRESENTATION_RE.search(normalized)
    if not match:
        # Users often say "coca de 500" or "big cola de 2" without the unit.
        # Treat numbers after "de/del" as presentation only in common bottle ranges.
        match = re.search(r"\b(?:de|del)\s+(\d+(?:[\.,]\d+)?)\b", normalized)
        if not match:
            return None

        raw_amount = match.group(1).replace(",", ".")
        try:
            number = float(raw_amount)
        except ValueError:
            return None

        if number >= 100 and number == int(number):
            return f"{int(number)}ml"
        if 0 < number <= 5:
            amount = str(int(number)) if number == int(number) else str(number).rstrip("0").rstrip(".")
            return f"{amount}L"
        return None

    amount = match.group(1).replace(",", ".")
    unit = match.group(2)
    if unit.startswith("m"):
        return f"{int(float(amount))}ml"
    if amount.endswith(".0"):
        amount = amount[:-2]
    return f"{amount}L"


def _detect_unit(value: str | None) -> str | None:
    match = UNIT_RE.search(_normalize(value))
    if not match:
        return None
    unit = match.group(1).replace(" ", "")
    if unit in {"cajas", "cajita", "cajitas"}:
        return "caja"
    if unit in {"latas"}:
        return "lata"
    if unit in {"sixpack"}:
        return "six pack"
    if unit in {"packs"}:
        return "pack"
    if unit in {"paquetes"}:
        return "paquete"
    return unit


def _strip_date_clause(value: str) -> str:
    return DATE_TRAILING_RE.sub("", value).strip()


def _base_clean_segment(segment: str) -> str:
    clean = _normalize(_strip_date_clause(segment))
    previous = None
    while clean and clean != previous:
        previous = clean
        clean = FILLER_RE.sub("", clean).strip()
    return clean


def _is_presentation_number(tokens: list[str], index: int) -> bool:
    previous_token = tokens[index - 1] if index > 0 else ""
    next_token = tokens[index + 1] if index + 1 < len(tokens) else ""
    current = tokens[index]
    if re.match(r"\d+(?:\.\d+)?(?:ml|l|lt|lts)$", current):
        return True
    return previous_token == "de" or next_token in PRESENTATION_UNIT_TOKENS


def _quantity_info(clean: str) -> tuple[int, int, int] | None:
    tokens = clean.split()
    for index, token in enumerate(tokens):
        next_token = tokens[index + 1] if index + 1 < len(tokens) else ""
        if re.fullmatch(r"x\d{1,3}", token):
            return max(1, int(token[1:])), index, index + 1

        if token == "x" and next_token.isdigit():
            return max(1, int(next_token)), index, index + 2

        if token.isdigit():
            if next_token not in COMMERCIAL_UNIT_TOKENS and _is_presentation_number(tokens, index):
                continue
            return max(1, int(token)), index, index + 1

        if token in QUANTITY_WORDS:
            if token in {"un", "una", "uno"} and next_token == "docena":
                return 12, index, index + 2
            if index > 0 and tokens[index - 1] == "de":
                continue
            if next_token in PRESENTATION_UNIT_TOKENS:
                continue
            return QUANTITY_WORDS[token], index, index + 1
    return None


def _quantity_start_end(tokens: list[str], index: int) -> tuple[int, int] | None:
    token = tokens[index]
    next_token = tokens[index + 1] if index + 1 < len(tokens) else ""

    if re.fullmatch(r"x\d{1,3}", token):
        return index, index + 1

    if token == "x" and next_token.isdigit():
        return index, index + 2

    if token.isdigit():
        if next_token not in COMMERCIAL_UNIT_TOKENS and _is_presentation_number(tokens, index):
            return None
        return index, index + 1

    if token in QUANTITY_WORDS:
        if token in {"un", "una", "uno"} and next_token == "docena":
            return index, index + 2
        if index > 0 and tokens[index - 1] == "de":
            return None
        if next_token in PRESENTATION_UNIT_TOKENS:
            return None
        return index, index + 1

    return None


def _split_quantity_runs(segment: str) -> list[str]:
    clean = _base_clean_segment(segment)
    tokens = clean.split()
    starts: list[int] = []

    index = 0
    while index < len(tokens):
        match = _quantity_start_end(tokens, index)
        if match:
            starts.append(match[0])
            index = max(index + 1, match[1])
            continue
        index += 1

    if len(starts) <= 1:
        return [segment.strip()] if segment.strip() else []

    parts: list[str] = []
    for start_index, start in enumerate(starts):
        end = starts[start_index + 1] if start_index + 1 < len(starts) else len(tokens)
        part = " ".join(tokens[start:end]).strip()
        if part:
            parts.append(part)
    return parts


def _split_order_segments(text: str) -> list[str]:
    coarse_segments = [part.strip() for part in SPLIT_RE.split(text or "") if part.strip()]
    if not coarse_segments and (text or "").strip():
        coarse_segments = [(text or "").strip()]

    segments: list[str] = []
    for segment in coarse_segments:
        segments.extend(_split_quantity_runs(segment))
    return [segment for segment in segments if segment]


def _quantity_detected(segment: str) -> bool:
    return _quantity_info(_base_clean_segment(segment)) is not None


def _item_fragment(segment: str) -> str:
    info = _quantity_info(segment)
    if info:
        _, start, _end = info
        return " ".join(segment.split()[start:])
    return segment


def _clean_segment(segment: str) -> str:
    clean = _base_clean_segment(segment)
    clean = _item_fragment(clean)
    return clean


def _parse_quantity(segment: str) -> int:
    info = _quantity_info(_base_clean_segment(segment))
    return info[0] if info else 1


def _remove_quantity(segment: str) -> str:
    clean = _clean_segment(segment)
    info = _quantity_info(clean)
    if info:
        _quantity, start, end = info
        tokens = clean.split()
        clean = " ".join(tokens[:start] + tokens[end:])
    tokens = clean.split()
    return clean.strip()


def _product_signal_text(clean_item: str) -> str:
    text = _normalize(clean_item)
    text = PRESENTATION_RE.sub("", text)
    text = UNIT_RE.sub("", text)
    tokens = []
    for token in text.split():
        clean_token = token.strip(".")
        if clean_token in NO_PRODUCT_SIGNAL_TOKENS or clean_token.isdigit():
            continue
        tokens.append(clean_token)
    return " ".join(tokens).strip()


def _has_product_signal(clean_item: str) -> bool:
    return bool(_product_signal_text(clean_item))


def _product_family(value: str | None) -> str:
    text = PRESENTATION_RE.sub("", _normalize(value)).strip()
    return re.sub(r"\s+", " ", text).strip()


def _needs_presentation_clarification(
    item: NLPParsedOrderItem,
    options: list[dict[str, Any]],
) -> bool:
    if _canonical_presentation(item.raw_text):
        return False
    if len(options) < 2:
        return False

    families = {_product_family(option.get("product")) for option in options}
    families.discard("")
    return len(families) == 1 and len({option.get("presentation") for option in options}) > 1


def _detected_product_text(clean_item: str) -> str | None:
    text = PRESENTATION_RE.sub("", clean_item)
    text = UNIT_RE.sub("", text)
    text = re.sub(
        r"\b(de|del|la|el|las|los|chica|chico|chika|chiko|grande|familiar|personal|litro|litros|ml|l)\b",
        " ",
        text,
    )
    text = re.sub(r"\s+", " ", text).strip()
    return text.title() if text else None


def _product_aliases(product: dict[str, Any], aliases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    product_name = product.get("name", "")
    generated: list[dict[str, Any]] = []

    for alias in _unit_variants(product_name):
        generated.append({"alias": alias, "weight": 1.0, "type": "official"})

    base_name = PRESENTATION_RE.sub("", _normalize(product_name)).strip()
    if base_name:
        generated.append({"alias": base_name, "weight": 0.72, "type": "product_only"})
        generated.append({"alias": re.sub(r"\bcola\b", "", base_name).strip(), "weight": 0.68, "type": "short_name"})

    # Specific rule for Agua Cielo (allows "agua" and "cielo" to match with presentations)
    presentation = _canonical_presentation(product_name)
    if "agua cielo" in base_name and presentation:
        for v in _unit_variants(f"agua {presentation}"):
            generated.append({"alias": v, "weight": 1.0, "type": "short_name_pres"})
        for v in _unit_variants(f"cielo {presentation}"):
            generated.append({"alias": v, "weight": 1.0, "type": "short_name_pres"})

    product_id = product.get("id")
    for alias in aliases:
        if alias.get("product_id") != product_id:
            continue
        generated.append({
            "alias": _normalize(alias.get("normalized_alias") or alias.get("alias_text")),
            "weight": float(alias.get("confidence_weight") or 1),
            "type": alias.get("alias_type") or "user_phrase",
        })

    unique: dict[str, dict[str, Any]] = {}
    for item in generated:
        alias_text = item["alias"]
        if not alias_text:
            continue
        if alias_text not in unique or item["weight"] > unique[alias_text]["weight"]:
            unique[alias_text] = item
    return list(unique.values())


def _fetch_aliases(db) -> list[dict[str, Any]]:
    try:
        return (
            db.table("product_aliases")
            .select("product_id, alias_text, normalized_alias, alias_type, confidence_weight")
            .eq("is_active", True)
            .execute()
            .data
            or []
        )
    except Exception:
        return []


def _score_alias(clean_item: str, alias: str, weight: float) -> float:
    score = 0.0
    for item_variant in _match_variants(clean_item):
        if alias and (alias in item_variant or item_variant in alias):
            score = max(score, 100.0)
        score = max(
            score,
            float(fuzz.WRatio(item_variant, alias)),
            float(fuzz.token_set_ratio(item_variant, alias)),
        )
    return min(100.0, score * weight)


def _brand_matches(clean_item: str, product: dict[str, Any], aliases: list[dict[str, Any]]) -> bool:
    """Validate that the query's brand/product signal matches the product brand or its aliases.

    If no brand/product name signal exists in the query, returns True (allows all candidates).
    Otherwise, the similarity score must be at least 65%.
    """
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

    # Also check spelling variants of query_signal against any of the product's aliases
    for alias_obj in _product_aliases(product, aliases):
        alias_text = alias_obj["alias"]
        alias_brand = _product_signal_text(alias_text)
        for q_var in query_variants:
            score = fuzz.WRatio(q_var, alias_brand)
            if score >= 65.0:
                return True

    return False


def _sku_candidates(clean_item: str, products: list[dict[str, Any]], aliases: list[dict[str, Any]]) -> list[NLPSkuCandidate]:
    candidates: dict[str, NLPSkuCandidate] = {}
    requested_presentation = _canonical_presentation(clean_item)

    for product in products:
        if not _brand_matches(clean_item, product, aliases):
            continue
        product_presentation = _canonical_presentation(product.get("name"))
        if requested_presentation and product_presentation != requested_presentation:
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
            presentation=product_presentation,
            score=round(best_score / 100, 2),
            stock=int(product.get("stock") or 0),
            price=float(product.get("price") or 0),
        )

    return sorted(candidates.values(), key=lambda item: item.score, reverse=True)[:4]


def _extract_delivery_date(text: str) -> str | None:
    normalized = _normalize(text)
    for pattern, replacement in TYPO_REPLACEMENTS:
        normalized = re.sub(pattern, replacement, normalized)
    today = date.today()
    if "pasado manana" in normalized:
        return (today + timedelta(days=2)).isoformat()
    if "manana" in normalized:
        return (today + timedelta(days=1)).isoformat()
    if re.search(r"\bhoy\b", normalized):
        return today.isoformat()

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
        if DATE_KEYWORD_RE.search(raw):
            return parsed.date().isoformat()
    return None


def _detect_store(db, user_id: str, text: str, requested_store_id: str | None) -> tuple[str | None, str | None]:
    if requested_store_id:
        return requested_store_id, None

    try:
        stores = db.table("stores").select("id, name").eq("user_id", user_id).execute().data or []
    except Exception:
        return None, None

    if len(stores) == 1:
        return stores[0]["id"], stores[0].get("name")

    normalized_text = _normalize(text)
    best_store = None
    best_score = 0
    for store in stores:
        name = _normalize(store.get("name"))
        if not name:
            continue
        score = max(fuzz.partial_ratio(normalized_text, name), fuzz.token_set_ratio(normalized_text, name))
        if score > best_score:
            best_score = score
            best_store = store

    if best_store and best_score >= 82:
        return best_store["id"], best_store.get("name")
    return None, None


def _looks_like_order_request(text: str | None) -> bool:
    normalized = _normalize(text)
    if not normalized:
        return False
    if ORDER_INTENT_RE.search(normalized):
        return True
    if re.search(r"\b\d{1,3}\b", normalized):
        return True
    return any(word in normalized.split() for word in QUANTITY_WORDS)


def _looks_like_product_fragment(text: str | None) -> bool:
    normalized = _normalize(text)
    if not normalized or normalized in COMMAND_TEXTS or normalized in GREETING_TEXTS:
        return False
    clean_item = _remove_quantity(text or "")
    signal = _product_signal_text(clean_item)
    return bool(signal and len(signal.split()) <= 5)


def _validation_for_items(items: list[NLPParsedOrderItem], delivery_date: str | None) -> tuple[str, list[NLPClarificationQuestion]]:
    questions: list[NLPClarificationQuestion] = []
    invalid = False

    for index, item in enumerate(items):
        if item.clarification_reason == "solid_food":
            questions.append(NLPClarificationQuestion(
                type="product",
                item_index=index,
                message=f"❌ *{item.producto_detectado or item.raw_text}* – Lamento informarte que no contamos con eso, ya que nos especializamos exclusivamente en el abastecimiento de productos líquidos y bebidas.",
            ))
            invalid = True
            continue

        if item.clarification_reason == "alcohol":
            questions.append(NLPClarificationQuestion(
                type="product",
                item_index=index,
                message=f"❌ *{item.producto_detectado or item.raw_text}* – Lamento informarte que no distribuimos bebidas alcohólicas.",
            ))
            invalid = True
            continue

        if not item.sku_candidates:
            questions.append(NLPClarificationQuestion(
                type="product",
                item_index=index,
                message=f"No encontre el producto '{item.raw_text}'. Especifica nombre y presentacion.",
            ))
            continue

        top = item.sku_candidates[0]
        second = item.sku_candidates[1] if len(item.sku_candidates) > 1 else None
        top_score = top.score * 100
        ambiguous = bool(second and (top.score - second.score) * 100 <= AMBIGUOUS_GAP)

        if top_score < CONFIRM_SCORE:
            questions.append(NLPClarificationQuestion(
                type="product",
                item_index=index,
                message=(
                    f"No encontre un producto activo que coincida con '{item.raw_text}'. "
                    "Revisa el nombre o pide el catalogo."
                ),
            ))
            continue
        elif top_score < AUTO_ACCEPT_SCORE or ambiguous:
            options = [
                candidate.model_dump()
                for candidate in item.sku_candidates
                if candidate.score * 100 >= CONFIRM_SCORE
            ][:3]
            needs_presentation = _needs_presentation_clarification(item, options)
            labels = " o ".join(
                str(candidate.get("presentation") or candidate.get("product") or "producto")
                for candidate in options
            )
            family = _product_family(top.product).title() or str(top.product or "producto")
            questions.append(NLPClarificationQuestion(
                type="presentation" if needs_presentation else "sku",
                item_index=index,
                message=(
                    f"¿Que presentacion quieres de {family}: {labels}?"
                    if needs_presentation
                    else f"Confirma si '{item.raw_text}' es {labels}."
                ),
                options=options,
            ))

        if not item.cantidad_detectada:
            questions.append(NLPClarificationQuestion(
                type="quantity",
                item_index=index,
                message=f"¿Cuantas unidades quieres de {item.producto_normalizado or item.producto_detectado or item.raw_text}?",
            ))

        if top.stock is not None and top.stock < item.cantidad:
            invalid = True
            questions.append(NLPClarificationQuestion(
                type="stock",
                item_index=index,
                message=f"No hay stock suficiente de {top.product}. Disponible: {top.stock}.",
                options=[top.model_dump()],
            ))

    if not delivery_date:
        questions.append(NLPClarificationQuestion(
            type="date",
            message="Indica la fecha de entrega, por ejemplo: manana o viernes.",
        ))
    else:
        try:
            parsed_dt = date.fromisoformat(delivery_date)
            if parsed_dt < date.today():
                questions.append(NLPClarificationQuestion(
                    type="date",
                    message="La fecha de entrega no puede ser en el pasado. Indica una fecha valida (hoy o despues):",
                ))
        except Exception:
            pass

    if invalid:
        return "invalid", questions
    if questions:
        return "requires_clarification", questions
    return "valid", questions



# Variant keywords that indicate a specific variety the user requested
_VARIANT_KEYWORDS = {
    "light", "zero", "sin azucar", "sin gas", "con gas", "naranja", "limon",
    "fresa", "mango", "tropical", "original", "clasica", "clasico",
}

# Non-beverage keywords that appear commonly in Bolivia
_NON_BEVERAGE_KEYWORDS = {
    "papa", "papas", "papita", "papitas", "nachos", "galleta", "galletas",
    "dulce", "dulces", "hamburguesa", "pizza", "sandwich", "bocadillo",
    "comida", "alimento", "snack", "chips", "popcorn", "canchita",
    "arroz", "fideo", "pan", "leche", "queso", "yogur", "yogurt",
}


def _requested_variant(raw_text: str) -> str | None:
    """Return the variant keyword found in the raw text, if any."""
    normalized = _normalize(raw_text)
    for keyword in _VARIANT_KEYWORDS:
        if keyword in normalized:
            return keyword
    return None


def _matched_name_contains_variant(matched_name: str, variant: str) -> bool:
    """Return True if the matched product name also contains the requested variant."""
    return variant in _normalize(matched_name)


def _is_non_beverage(raw_text: str) -> bool:
    """Return True if the raw text looks like a non-beverage item."""
    normalized = _normalize(raw_text)
    tokens = set(normalized.split())
    return bool(tokens & _NON_BEVERAGE_KEYWORDS)


def _suggest_alternative(raw_text: str) -> str:
    """Return a product-specific alternative suggestion based on the raw text."""
    lower = raw_text.lower()
    if "coca" in lower or "cola" in lower:
        return "si tengo Coca-Cola Normal (2L, 1.5L, 500ml)"
    if "agua" in lower or "cielo" in lower or "vital" in lower:
        return "si tengo Agua Cielo y Agua Vital sin gas"
    if "volt" in lower:
        return "si tengo Volt de 300ml y 500ml"
    if "big" in lower or "big cola" in lower:
        return "si tengo Big Cola en varias presentaciones"
    if "pulp" in lower:
        return "si tengo Pulp Naranja y Pulp Durazno"
    if "cifrut" in lower:
        return "si tengo Cifrut en distintos sabores"
    return "puedes pedir el menu para ver lo que tenemos disponible"


def _build_message(response: NLPParseOrderResponse) -> str:
    if not response.items:
        return "No pude identificar productos. Escribe cantidad, producto y presentacion."

    responses = []
    has_issues = False
    questions_by_item: dict[int, list[NLPClarificationQuestion]] = {}
    for question in response.clarification_questions:
        if question.item_index is None:
            continue
        questions_by_item.setdefault(question.item_index, []).append(question)

    for index, item in enumerate(response.items):
        prefix = "-"

        # 1. Solid food
        if item.clarification_reason == "solid_food" or _is_non_beverage(item.raw_text):
            responses.append(
                f"{prefix} {item.producto_detectado or item.raw_text}: "
                "No vendemos ese producto. Somos una empresa de bebidas y solo "
                "distribuimos productos liquidos."
            )
            has_issues = True
            continue

        # 2. Alcohol
        if item.clarification_reason == "alcohol":
            responses.append(
                f"{prefix} {item.producto_detectado or item.raw_text}: "
                "No distribuimos bebidas alcoholicas."
            )
            has_issues = True
            continue

        # 3. No SKU candidates found
        if not item.sku_candidates:
            alt = _suggest_alternative(item.raw_text)
            responses.append(
                f"{prefix} {item.raw_text}: No tengo ese producto, pero {alt}. "
                "Deseas cambiarlo?"
            )
            has_issues = True
            continue

        top = item.sku_candidates[0]
        top_score = top.score * 100
        second = item.sku_candidates[1] if len(item.sku_candidates) > 1 else None

        # 4. Low confidence match
        if top_score < CONFIRM_SCORE:
            alt = _suggest_alternative(item.raw_text)
            responses.append(
                f"{prefix} {item.raw_text}: No tengo ese producto exacto, pero {alt}. "
                "Deseas cambiarlo?"
            )
            has_issues = True
            continue

        # 5. Variant mismatch: user asked for "Light" but matched "2L"
        requested_variant = _requested_variant(item.raw_text)
        matched_name = top.product or ""
        if requested_variant and not _matched_name_contains_variant(matched_name, requested_variant):
            alt = _suggest_alternative(item.raw_text)
            responses.append(
                f"{prefix} {item.raw_text}: No tengo esa variante, pero {alt}. "
                "Deseas alguna de esas?"
            )
            has_issues = True
            continue

        # 6. Ambiguous product/presentation: show the same clarification that
        # was persisted, so the next short reply resolves the visible question.
        item_questions = questions_by_item.get(index, [])
        match_question = next(
            (question for question in item_questions if question.type in {"presentation", "sku"}),
            None,
        )
        if item.requires_clarification and match_question:
            responses.append(f"{prefix} {match_question.message}")
            has_issues = True
            continue

        # 7. Stock issue
        if top.stock is not None and top.stock < item.cantidad:
            responses.append(
                f"{prefix} {top.product}: No tengo suficiente stock. "
                f"Disponible: {top.stock} unidades."
            )
            has_issues = True
            continue

        # 8. Quantity not detected
        if not item.cantidad_detectada:
            responses.append(
                f"{prefix} {top.product}: Cuantas unidades deseas?"
            )
            has_issues = True
            continue

        # 9. All good - product found and matched
        name = item.producto_normalizado or top.product
        presentation = f" {item.presentacion}" if item.presentacion else ""
        if presentation and presentation.strip().lower() in name.lower():
            presentation = ""
        qty = item.cantidad
        responses.append(f"{prefix} {qty} x {name}{presentation} - Anotado.")

    global_questions = [
        question for question in response.clarification_questions
        if question.item_index is None
    ]
    for question in global_questions:
        responses.append(f"- {question.message}")
        has_issues = True

    greeting = "Con gusto proceso tu pedido.\n\n"
    items_list = "\n".join(responses)

    if has_issues:
        footer = "\n\nHay algo que quieras ajustar o agregar?"
    else:
        date_copy = f"Entrega: {response.fecha_entrega}. " if response.fecha_entrega else ""
        footer = f"\n\n{date_copy}Confirmas los productos?"

    return f"{greeting}{items_list}{footer}"



def _action_line(payload: dict[str, Any]) -> str:
    import json

    return f"{CHAT_ACTION_PREFIX}{json.dumps(payload, ensure_ascii=True, separators=(',', ':'))}"


def _money(value: Any) -> str:
    try:
        return f"Bs {float(value or 0):.2f}"
    except (TypeError, ValueError):
        return "Bs 0.00"


def _store_name(db, store_id: str | None) -> str:
    if not store_id:
        return "Sin tienda"
    result = db.table("stores").select("name").eq("id", store_id).execute()
    return result.data[0]["name"] if result.data else "Sin tienda"


def _order_out(db, order: dict[str, Any], item_rows: list[dict[str, Any]]) -> OrderOut:
    items: list[OrderItemOut] = []
    for row in item_rows:
        product = db.table("products").select("name").eq("id", row["product_id"]).execute()
        product_name = product.data[0]["name"] if product.data else "Producto"
        items.append(OrderItemOut(
            id=row["id"],
            order_id=row["order_id"],
            product_id=row["product_id"],
            product_name=product_name,
            quantity=row["quantity"],
            unit_price=row["unit_price"],
            subtotal=row["subtotal"],
        ))

    return OrderOut(
        id=order["id"],
        user_id=order["user_id"],
        store_id=order["store_id"],
        store_name=_store_name(db, order.get("store_id")),
        status=order["status"],
        delivery_date=str(order.get("delivery_date")) if order.get("delivery_date") else None,
        total=order["total"],
        notes=order.get("notes"),
        created_at=order.get("created_at"),
        items=items,
        nlp_data=order.get("nlp_data"),
    )


def _draft_detail_message(order: OrderOut, *, updated: bool = False) -> str:
    lines = [
        f"Borrador #{order.id[:8]} {'actualizado' if updated else 'creado'}.",
        f"Tienda: {order.store_name or 'Sin tienda'}",
        f"Entrega: {order.delivery_date or 'sin fecha'}",
        "Detalle:",
    ]

    for item in order.items or []:
        lines.append(
            f"- {item.quantity} x {item.product_name or 'Producto'} "
            f"({_money(item.unit_price)} c/u) = {_money(item.subtotal)}"
        )

    lines.extend([
        f"Total: {_money(order.total)}",
        "Estado: Borrador. Confirma para enviarlo a AJE y pasarlo a Pendiente.",
        _action_line({
            "type": "confirm_order",
            "order_id": order.id,
            "label": "Confirmar y enviar a AJE",
            "status": "Borrador",
            "total": _money(order.total),
            "delivery": order.delivery_date,
        }),
        _action_line({
            "type": "order",
            "order_id": order.id,
            "label": f"Ver borrador #{order.id[:8]}",
            "store": order.store_name,
            "status": "Borrador",
            "total": _money(order.total),
            "delivery": order.delivery_date,
        }),
    ])
    return "\n".join(lines)


def _fetch_draft_order(db, *, user_id: str, order_id: str | None) -> dict[str, Any] | None:
    if not order_id:
        return None
    result = (
        db.table("orders")
        .select("*")
        .eq("id", order_id)
        .eq("user_id", user_id)
        .eq("status", "borrador")
        .limit(1)
        .execute()
        .data
    )
    return result[0] if result else None


def _append_items_to_draft_from_response(
    db,
    *,
    user_id: str,
    raw_text: str,
    order: dict[str, Any],
    response: NLPParseOrderResponse,
) -> OrderOut:
    if response.requires_clarification or response.validation_status != "valid":
        raise HTTPException(status_code=400, detail="La extraccion NLP aun requiere aclaracion")

    items_to_insert: list[dict[str, Any]] = []
    added_total = 0.0
    for item in response.items:
        product_id = item.product_id or item.sku_id
        if not product_id:
            raise HTTPException(status_code=400, detail=f"SKU no resuelto para {item.raw_text}")

        product_result = db.table("products").select("*").eq("id", product_id).eq("active", True).execute()
        if not product_result.data:
            raise HTTPException(status_code=400, detail=f"Producto {product_id} no encontrado o inactivo")

        product = product_result.data[0]
        if int(product.get("stock") or 0) < item.cantidad:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para {product['name']}. Disponible: {product['stock']}, Solicitado: {item.cantidad}",
            )

        unit_price = float(product.get("price") or 0)
        subtotal = unit_price * item.cantidad
        added_total += subtotal
        items_to_insert.append({
            "order_id": order["id"],
            "product_id": product_id,
            "quantity": item.cantidad,
            "unit_price": unit_price,
            "subtotal": subtotal,
        })

    if items_to_insert:
        db.table("order_items").insert(items_to_insert).execute()

    nlp_data = order.get("nlp_data") or {}
    history = list(nlp_data.get("updates") or [])
    history.append({
        "raw_text": raw_text,
        "parsed": response.model_dump(exclude_none=True),
    })
    nlp_data["updates"] = history[-20:]

    updated = (
        db.table("orders")
        .update({
            "total": float(order.get("total") or 0) + added_total,
            "nlp_data": nlp_data,
        })
        .eq("id", order["id"])
        .eq("user_id", user_id)
        .execute()
        .data
    )
    updated_order = updated[0] if updated else order
    item_rows = db.table("order_items").select("*").eq("order_id", order["id"]).execute().data or []
    return _order_out(db, updated_order, item_rows)


def _append_items_to_draft_from_text(
    db,
    *,
    text: str,
    user_id: str,
    order_id: str | None,
) -> str | None:
    if not (_looks_like_product_fragment(text) or _looks_like_order_request(text)):
        return None

    order = _fetch_draft_order(db, user_id=user_id, order_id=order_id)
    if not order:
        return None

    parsed = _parse_order_payload(
        db,
        text=text,
        user_id=user_id,
        requested_store_id=order.get("store_id"),
        persist=True,
        require_store=True,
        default_delivery_date=order.get("delivery_date"),
    )

    if parsed.requires_clarification or parsed.validation_status != "valid":
        return parsed.message

    updated_order = _append_items_to_draft_from_response(
        db,
        user_id=user_id,
        raw_text=text,
        order=order,
        response=parsed,
    )
    return _draft_detail_message(updated_order, updated=True)


def _create_draft_from_nlp_response(
    db,
    *,
    user_id: str,
    raw_text: str,
    response: NLPParseOrderResponse,
) -> OrderOut:
    if response.requires_clarification or response.validation_status != "valid":
        raise HTTPException(status_code=400, detail="La extraccion NLP aun requiere aclaracion")
    if not response.store_id:
        raise HTTPException(status_code=400, detail="Falta tienda para crear el borrador")
    if not response.fecha_entrega:
        raise HTTPException(status_code=400, detail="Falta fecha de entrega para crear el borrador")

    store = db.table("stores").select("id").eq("id", response.store_id).eq("user_id", user_id).execute()
    if not store.data:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")

    total = 0.0
    items_to_insert: list[dict[str, Any]] = []
    for item in response.items:
        product_id = item.product_id or item.sku_id
        if not product_id:
            raise HTTPException(status_code=400, detail=f"SKU no resuelto para {item.raw_text}")

        product_result = db.table("products").select("*").eq("id", product_id).eq("active", True).execute()
        if not product_result.data:
            raise HTTPException(status_code=400, detail=f"Producto {product_id} no encontrado o inactivo")

        product = product_result.data[0]
        if int(product.get("stock") or 0) < item.cantidad:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para {product['name']}. Disponible: {product['stock']}, Solicitado: {item.cantidad}",
            )

        unit_price = float(product.get("price") or 0)
        subtotal = unit_price * item.cantidad
        total += subtotal
        items_to_insert.append({
            "product_id": product_id,
            "quantity": item.cantidad,
            "unit_price": unit_price,
            "subtotal": subtotal,
        })

    nlp_data = response.model_dump(exclude_none=True)
    nlp_data.pop("interaction_id", None)
    order_result = db.table("orders").insert({
        "user_id": user_id,
        "store_id": response.store_id,
        "status": "borrador",
        "delivery_date": response.fecha_entrega,
        "total": total,
        "notes": f"Creado desde NLP: {raw_text[:180]}",
        "nlp_data": nlp_data,
    }).execute()
    if not order_result.data:
        raise HTTPException(status_code=500, detail="Error al crear el borrador")

    order = order_result.data[0]
    for row in items_to_insert:
        row["order_id"] = order["id"]
    item_rows = db.table("order_items").insert(items_to_insert).execute().data or []
    return _order_out(db, order, item_rows)


def _persist_interaction(
    db,
    *,
    user_id: str,
    store_id: str | None,
    text: str,
    response: NLPParseOrderResponse,
) -> str | None:
    payload = response.model_dump(exclude_none=True)
    payload.pop("interaction_id", None)

    try:
        result = db.table("nlp_interactions").insert({
            "user_id": user_id,
            "store_id": store_id,
            "raw_text": text,
            "normalized_text": _normalize(text),
            "detected_intent": response.intent,
            "extracted_json": payload,
            "confidence_score": response.confidence_score,
            "validation_status": response.validation_status,
            "requires_human_review": response.requires_clarification,
            "clarification_questions": [q.model_dump(exclude_none=True) for q in response.clarification_questions],
        }).execute()
    except Exception:
        return None

    if not result.data:
        return None

    interaction_id = result.data[0]["id"]
    for question in response.clarification_questions:
        try:
            db.table("clarification_events").insert({
                "interaction_id": interaction_id,
                "user_id": user_id,
                "store_id": store_id,
                "question_type": question.type,
                "question_text": question.message,
                "options": question.options,
                "resolved": False,
            }).execute()
        except Exception:
            continue
    return interaction_id


def _parse_order_payload(
    db,
    *,
    text: str,
    user_id: str,
    requested_store_id: str | None = None,
    persist: bool = True,
    require_store: bool = True,
    default_delivery_date: str | None = None,
) -> NLPParseOrderResponse:
    clean_text = (text or "").strip()
    products = db.table("products").select("*").eq("active", True).execute().data or []
    aliases = _fetch_aliases(db)
    delivery_date = _extract_delivery_date(clean_text) or default_delivery_date
    store_id, detected_store_name = _detect_store(db, user_id, clean_text, requested_store_id)

    segments = _split_order_segments(clean_text)

    items: list[NLPParsedOrderItem] = []
    for segment in segments:
        clean_item = _remove_quantity(segment)
        if not clean_item or DATE_KEYWORD_RE.fullmatch(clean_item):
            continue

        # Check for solid food
        is_solid = any(word in clean_item.split() for word in SOLID_KEYWORDS)
        # Check for alcohol
        is_alcohol = any(word in clean_item.split() for word in ALCOHOL_KEYWORDS)

        if is_solid or is_alcohol:
            items.append(NLPParsedOrderItem(
                raw_text=segment,
                producto_detectado=clean_item,
                producto_normalizado=None,
                presentacion=None,
                unidad=None,
                cantidad=1,
                cantidad_detectada=False,
                sku_id=None,
                product_id=None,
                confidence=0.0,
                sku_candidates=[],
                requires_clarification=True,
                clarification_reason="solid_food" if is_solid else "alcohol",
            ))
            continue

        if not _has_product_signal(clean_item):
            continue

        candidates = _sku_candidates(clean_item, products, aliases)
        quantity = _parse_quantity(segment)
        quantity_detected = _quantity_detected(segment)
        top = candidates[0] if candidates else None
        confidence = top.score if top else 0.0

        top_score = confidence * 100
        second = candidates[1] if len(candidates) > 1 else None
        ambiguous = bool(second and (confidence - second.score) * 100 <= AMBIGUOUS_GAP)
        accepted = bool(top and quantity_detected and top_score >= AUTO_ACCEPT_SCORE and not ambiguous)
        recognized_top = top if top and top_score >= CONFIRM_SCORE else None

        reason = None
        if not quantity_detected:
            reason = "quantity_missing"
        elif not top:
            reason = "product_not_found"
        elif top_score < AUTO_ACCEPT_SCORE or ambiguous:
            reason = "low_confidence_or_ambiguous"
        elif top.stock is not None and top.stock < quantity:
            reason = "insufficient_stock"

        items.append(NLPParsedOrderItem(
            raw_text=segment,
            producto_detectado=_detected_product_text(clean_item),
            producto_normalizado=recognized_top.product if recognized_top else None,
            presentacion=recognized_top.presentation if recognized_top else _canonical_presentation(clean_item),
            unidad=_detect_unit(clean_item),
            cantidad=quantity,
            cantidad_detectada=quantity_detected,
            sku_id=top.sku_id if accepted else None,
            product_id=top.product_id if accepted else None,
            confidence=confidence,
            sku_candidates=candidates,
            requires_clarification=not accepted,
            clarification_reason=reason,
        ))

    validation_status, questions = _validation_for_items(items, delivery_date)
    if not items:
        validation_status = "requires_clarification"
        questions.insert(0, NLPClarificationQuestion(
            type="product",
            message="No encontre productos en el pedido. Indica cantidad, producto y presentacion.",
        ))

    if require_store and not store_id:
        questions.append(NLPClarificationQuestion(
            type="customer",
            message="Selecciona o indica la tienda/cliente para asociar el pedido.",
        ))
        validation_status = "requires_clarification" if validation_status == "valid" else validation_status

    confidence_score = round(sum(item.confidence for item in items) / len(items), 2) if items else 0.0
    response = NLPParseOrderResponse(
        intent="crear_pedido",
        store_id=store_id,
        customer_id=store_id,
        fecha_entrega=delivery_date,
        items=items,
        requires_clarification=bool(questions),
        clarification_questions=questions,
        validation_status=validation_status,
        confidence_score=confidence_score,
        message=None,
    )
    response.message = _build_message(response)

    if detected_store_name and response.message and not response.requires_clarification:
        response.message = f"Tienda detectada: {detected_store_name}. {response.message}"

    if persist:
        response.interaction_id = _persist_interaction(
            db,
            user_id=user_id,
            store_id=store_id,
            text=clean_text,
            response=response,
        )

    return response


@router.post("/parse-order", response_model=NLPParseOrderResponse)
async def parse_order_structured(body: NLPParseOrderRequest, user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    requested_store_id = body.store_id or body.customer_id
    return _parse_order_payload(
        db,
        text=body.text,
        user_id=user_id,
        requested_store_id=requested_store_id,
        persist=True,
        require_store=True,
    )


def _draft_order_payload(
    db,
    *,
    text: str,
    user_id: str,
    requested_store_id: str | None = None,
    persist: bool = True,
) -> NLPDraftOrderResponse:
    parsed = _parse_order_payload(
        db,
        text=text,
        user_id=user_id,
        requested_store_id=requested_store_id,
        persist=persist,
        require_store=True,
    )

    draft_response = NLPDraftOrderResponse(
        **parsed.model_dump(),
        draft_created=False,
        order=None,
    )

    if parsed.requires_clarification or parsed.validation_status != "valid":
        return draft_response

    order = _create_draft_from_nlp_response(
        db,
        user_id=user_id,
        raw_text=text,
        response=parsed,
    )
    draft_response.draft_created = True
    draft_response.order = order
    draft_response.message = _draft_detail_message(order)
    return draft_response


def _last_pending_order_text(db, *, user_id: str) -> str | None:
    try:
        rows = (
            db.table("nlp_interactions")
            .select("raw_text, validation_status, requires_human_review")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(8)
            .execute()
            .data
            or []
        )
    except Exception:
        return None

    for row in rows:
        raw_text = str(row.get("raw_text") or "").strip()
        if not raw_text:
            continue
        if row.get("validation_status") == "requires_clarification" or row.get("requires_human_review"):
            return raw_text
    return None


def _last_pending_clarification(db, *, user_id: str) -> dict[str, Any] | None:
    """Return the first unresolved clarification from the user's most recent interaction."""
    events = _last_pending_clarifications(db, user_id=user_id)
    return events[0] if events else None


def _last_pending_clarifications(db, *, user_id: str) -> list[dict[str, Any]]:
    """Return unresolved clarifications from the user's most recent interaction."""
    try:
        latest = (
            db.table("clarification_events")
            .select("interaction_id")
            .eq("user_id", user_id)
            .eq("resolved", False)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
            .data
        )
        if not latest:
            return []
        interaction_id = latest[0].get("interaction_id")
        if not interaction_id:
            return []
        events = (
            db.table("clarification_events")
            .select("*")
            .eq("interaction_id", interaction_id)
            .eq("resolved", False)
            .order("created_at")
            .execute()
            .data
        )
        if not events:
            return []

        fresh_events = []
        for event in events:
            created_at_str = event.get("created_at")
            if created_at_str:
                if created_at_str.endswith("Z"):
                    created_at_str = created_at_str[:-1] + "+00:00"
                try:
                    created_at_dt = datetime.fromisoformat(created_at_str)
                    now = datetime.now(timezone.utc)
                    if (now - created_at_dt).total_seconds() > MAX_CLARIFICATION_AGE_SECONDS:
                        continue
                except Exception:
                    pass
            fresh_events.append(event)
        return fresh_events
    except Exception:
        return []


_BRANDS = {"coca", "cola", "cielo", "agua", "volt", "oro", "pulp", "cifrut", "sporade", "tea"}

def _get_brand_keywords(text: str) -> set[str]:
    words = {w.strip(".,!?()-\"'/") for w in text.lower().split()}
    return words & _BRANDS

def _is_valid_clarification_reply_for_pending(text: str, pending: dict[str, Any]) -> bool:
    user_brands = _get_brand_keywords(text)
    if not user_brands:
        return True
        
    pending_text_source = []
    q_text = pending.get("question_text")
    if q_text:
        pending_text_source.append(q_text)
        
    options = pending.get("options") or []
    for opt in options:
        p_name = opt.get("product")
        if p_name:
            pending_text_source.append(p_name)
            
    pending_combined = " ".join(pending_text_source)
    pending_brands = _get_brand_keywords(pending_combined)
    
    if user_brands - pending_brands:
        return False
        
    return True


def _matching_pending_clarification(
    db,
    *,
    user_id: str,
    text: str,
) -> tuple[dict[str, Any], str] | tuple[None, None]:
    for pending in _last_pending_clarifications(db, user_id=user_id):
        if not _is_valid_clarification_reply_for_pending(text, pending):
            continue
        enriched = _interpret_clarification_reply(
            db, text=text, clarification=pending,
        )
        if enriched:
            return pending, enriched
    return None, None


def _resolve_clarification(db, clarification_id: str, answer_text: str) -> None:
    """Mark a clarification event as resolved with the user's answer."""
    try:
        db.table("clarification_events").update({
            "resolved": True,
            "answer_text": answer_text,
        }).eq("id", clarification_id).execute()
    except Exception:
        pass


def _is_clarification_reply(text: str) -> bool:
    """Check if text looks like a short reply to a pending clarification."""
    normalized = _normalize(text)
    if not normalized:
        return False
    if normalized in COMMAND_TEXTS or normalized in GREETING_TEXTS:
        return False
    return True


def _match_presentation_option(
    text: str, options: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Match a user reply to one of the presentation/SKU options."""
    if not options:
        return None
    normalized = _normalize(text)

    # Already a canonical presentation? ("1l", "500ml", etc.)
    canonical = _canonical_presentation(text)
    if canonical:
        for option in options:
            if (option.get("presentation") or "").upper() == canonical.upper():
                return option

    # Extract a bare number ("1", "500", "2.5")
    num_match = re.fullmatch(r"(\d+(?:[.,]\d+)?)", normalized)
    if not num_match:
        return None
    raw_number = num_match.group(1).replace(",", ".")
    try:
        number = float(raw_number)
    except ValueError:
        return None

    # Try as liters first ("1" → "1L", "2.5" → "2.5L")
    liter_str = f"{int(number)}L" if number == int(number) else f"{number}L"
    for option in options:
        if (option.get("presentation") or "").upper() == liter_str.upper():
            return option

    # Try as milliliters ("500" → "500ml")
    if number == int(number) and number >= 100:
        ml_str = f"{int(number)}ml"
        for option in options:
            if (option.get("presentation") or "").upper() == ml_str.upper():
                return option

    return None


def _match_option_by_index(
    text: str, options: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Interpret text as a 1-based index into the options list."""
    normalized = _normalize(text)
    if not normalized.isdigit():
        return None
    index = int(normalized) - 1
    if 0 <= index < len(options):
        return options[index]
    return None


def _get_interaction_raw_text(db, interaction_id: str | None) -> str:
    """Fetch the original raw_text from an nlp_interaction."""
    if not interaction_id:
        return ""
    try:
        rows = (
            db.table("nlp_interactions")
            .select("raw_text")
            .eq("id", interaction_id)
            .limit(1)
            .execute()
            .data
        )
        return str(rows[0].get("raw_text") or "").strip() if rows else ""
    except Exception:
        return ""


def _build_enriched_text(original_raw: str, product_name: str) -> str:
    """Build enriched text preserving the original quantity and date context."""
    if not product_name:
        return original_raw
    
    qty_prefix = ""
    if original_raw and _quantity_detected(original_raw):
        qty = _parse_quantity(original_raw)
        qty_prefix = f"{qty} "
        
    date_suffix = ""
    if original_raw:
        match = DATE_TRAILING_RE.search(original_raw)
        if match:
            date_suffix = f" {match.group(0).strip()}"
            
    return f"{qty_prefix}{product_name}{date_suffix}"


def _interpret_clarification_reply(
    db,
    *,
    text: str,
    clarification: dict[str, Any],
) -> str | None:
    """Interpret a short reply using the context of a pending clarification.

    Returns an enriched text suitable for re-parsing, or None.
    """
    question_type = clarification.get("question_type", "")
    options = clarification.get("options") or []
    interaction_id = clarification.get("interaction_id")
    original_raw = _get_interaction_raw_text(db, interaction_id)

    if question_type == "presentation":
        # Priority: literal presentation match, then index
        matched = _match_presentation_option(text, options)
        if not matched:
            matched = _match_option_by_index(text, options)
        if matched:
            return _build_enriched_text(original_raw, matched.get("product", ""))

    elif question_type in ("sku", "product"):
        # Interpret affirmation as confirming the top option
        normalized = _normalize(text)
        if normalized in {"si", "si.", "si,", "sí", "ok", "okay", "correcto", "dale", "yes"}:
            if options:
                return _build_enriched_text(original_raw, options[0].get("product", ""))

        matched = _match_presentation_option(text, options)
        if not matched:
            matched = _match_option_by_index(text, options)
        if matched:
            return _build_enriched_text(original_raw, matched.get("product", ""))

    elif question_type == "quantity":
        normalized = _normalize(text)
        qty = None
        if normalized.isdigit():
            qty = int(normalized)
        elif normalized in QUANTITY_WORDS:
            qty = QUANTITY_WORDS[normalized]
        if qty is not None and original_raw:
            return f"{qty} {original_raw}"

    elif question_type == "date":
        if original_raw:
            return f"{original_raw} para {text}"

    return None


def _context_order_text(db, *, user_id: str, context: dict[str, Any] | None = None) -> str | None:
    context_text = str((context or {}).get("pending_order_text") or "").strip()
    if context_text:
        return context_text
    return None


def _should_extend_order_context(text: str) -> bool:
    normalized = _normalize(text)
    if not normalized:
        return False
    if normalized in COMMAND_TEXTS or normalized in GREETING_TEXTS:
        return False
    if CONTEXT_APPEND_RE.search(text or ""):
        return True
    clean_item = _remove_quantity(text)
    has_product_signal = _has_product_signal(clean_item)
    if ORDER_INTENT_RE.search(normalized) and has_product_signal:
        return False
    if _quantity_detected(text) and has_product_signal:
        return False
    if _extract_delivery_date(text) and not has_product_signal:
        return True
    if not has_product_signal:
        return True
    if not _quantity_detected(text):
        return True
    return False


def _should_parse_before_context(text: str) -> bool:
    normalized = _normalize(text)
    if not normalized or normalized in COMMAND_TEXTS or normalized in GREETING_TEXTS:
        return False
    if CONTEXTUAL_REPLY_RE.search(text or ""):
        return False
    return _looks_like_product_fragment(text)


def _merge_context_text(context_text: str | None, text: str) -> str | None:
    previous = (context_text or "").strip()
    current = (text or "").strip()
    if not previous or not current:
        return None
    if _normalize(previous) == _normalize(current):
        return None
    return f"{previous} {current}"


def _family_key(value: str | None) -> str:
    text = PRESENTATION_RE.sub("", _normalize(value)).replace("-", " ")
    text = re.sub(r"\b(light|normal)\b", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _parsed_item_name(item: NLPParsedOrderItem) -> str | None:
    if item.producto_normalizado:
        return item.producto_normalizado
    if item.sku_candidates:
        return item.sku_candidates[0].product
    return item.producto_detectado or item.raw_text


def _delivery_suffix_from_context(*texts: str | None) -> str:
    for value in texts:
        normalized = _normalize(value)
        for pattern, replacement in TYPO_REPLACEMENTS:
            normalized = re.sub(pattern, replacement, normalized)
        if "pasado manana" in normalized:
            return " para pasado manana"
        if "manana" in normalized:
            return " para manana"
        if re.search(r"\bhoy\b", normalized):
            return " para hoy"
    return ""


def _contextual_correction_text(
    db,
    *,
    user_id: str,
    context_text: str | None,
    text: str,
    requested_store_id: str | None = None,
) -> str | None:
    """Build a corrected order from a follow-up using quantities from context.

    Example:
      context: "Para maniana quiero 4 volt y 2 coca light"
      reply:   "Volt de 300 y si coca cola de 2 litros"
      output:  "4 Volt 300ml y 2 Coca-Cola 2L para manana"
    """
    previous = (context_text or "").strip()
    current = (text or "").strip()
    if not previous or not current:
        return None
    if _quantity_detected(current):
        return None

    base = _parse_order_payload(
        db,
        text=previous,
        user_id=user_id,
        requested_store_id=requested_store_id,
        persist=False,
        require_store=False,
    )
    followup = _parse_order_payload(
        db,
        text=current,
        user_id=user_id,
        requested_store_id=requested_store_id,
        persist=False,
        require_store=False,
    )

    quantities_by_family: dict[str, int] = {}
    for item in base.items:
        if not item.cantidad_detectada:
            continue
        family = _family_key(_parsed_item_name(item))
        if family:
            quantities_by_family.setdefault(family, item.cantidad)

    parts: list[str] = []
    used_families: set[str] = set()
    for item in followup.items:
        if not item.sku_candidates:
            continue
        name = item.producto_normalizado or item.sku_candidates[0].product
        family = _family_key(name)
        if not name or not family or family in used_families:
            continue
        quantity = quantities_by_family.get(family)
        if not quantity:
            continue
        parts.append(f"{quantity} {name}")
        used_families.add(family)

    if not parts:
        return None
    return " y ".join(parts) + _delivery_suffix_from_context(previous, current)


def _is_negation_only(text: str) -> bool:
    """Returns True if the message is a pure negation without a product request."""
    normalized = _normalize(text)
    # Phrases like: no, no gracias, no quiero nada, no por ahora
    pure_negation = {"no", "no gracias", "no por ahora", "no quiero nada", "ninguno", "nada", "no nada"}
    return normalized in pure_negation


def _extract_solo_product(text: str) -> str | None:
    """Extract product from 'solo X', 'solo agua porfavor', 'mejor solo agua', etc."""
    normalized = _normalize(text)
    # Match 'solo X' or 'mejor solo X' or 'nada mas X'
    for prefix in ("solo ", "mejor solo ", "nada mas ", "nomás ", "nomas ", "solamente "):
        if normalized.startswith(prefix):
            candidate = normalized[len(prefix):].strip()
            # Remove trailing fillers
            for filler in (" porfavor", " por favor", " please", " gracias", " porf"):
                candidate = candidate.removesuffix(filler)
            return candidate.strip() if candidate else None
    return None


def draft_order_chat_reply(
    db,
    *,
    text: str,
    user_id: str,
    requested_store_id: str | None = None,
    active_order_id: str | None = None,
    context: dict[str, Any] | None = None,
) -> str | None:
    # ── Handle pure negations (no, no gracias, etc.) ──────────────
    if _is_negation_only(text):
        return "Entendido. Si cambias de idea o quieres pedir algo, estoy aqui para ayudarte."

    # ── Handle 'solo X' patterns (user correcting previous suggestion) ──
    solo_product = _extract_solo_product(text)
    if solo_product:
        # Treat as a fresh product request with the extracted product
        enriched = solo_product
        response = _draft_order_payload(
            db,
            text=enriched,
            user_id=user_id,
            requested_store_id=requested_store_id,
            persist=True,
        )
        if response.draft_created:
            return response.message
        if response.items or response.clarification_questions:
            return response.message

    # ── Handle pending clarification replies ──────────────────────
    if _is_clarification_reply(text):
        pending, enriched = _matching_pending_clarification(
            db, user_id=user_id, text=text,
        )
        if pending and enriched:
            _resolve_clarification(
                db, pending.get("id", ""), text,
            )
            store_id = pending.get("store_id") or requested_store_id

            if active_order_id:
                order = _fetch_draft_order(db, user_id=user_id, order_id=active_order_id)
                if order:
                    parsed = _parse_order_payload(
                        db,
                        text=enriched,
                        user_id=user_id,
                        requested_store_id=order.get("store_id"),
                        persist=True,
                        require_store=True,
                        default_delivery_date=order.get("delivery_date"),
                    )
                    if parsed.requires_clarification or parsed.validation_status != "valid":
                        return parsed.message

                    updated_order = _append_items_to_draft_from_response(
                        db,
                        user_id=user_id,
                        raw_text=enriched,
                        order=order,
                        response=parsed,
                    )
                    return _draft_detail_message(updated_order, updated=True)

            response = _draft_order_payload(
                db,
                text=enriched,
                user_id=user_id,
                requested_store_id=store_id,
                persist=True,
            )
            if response.draft_created:
                return response.message
            if response.items or response.clarification_questions:
                return response.message

    if active_order_id:
        draft_reply = _append_items_to_draft_from_text(
            db,
            text=text,
            user_id=user_id,
            order_id=active_order_id,
        )
        if draft_reply:
            return draft_reply

    context_text = _context_order_text(db, user_id=user_id, context=context)

    contextual_text = _contextual_correction_text(
        db,
        user_id=user_id,
        context_text=context_text,
        text=text,
        requested_store_id=requested_store_id,
    )
    if contextual_text:
        response = _draft_order_payload(
            db,
            text=contextual_text,
            user_id=user_id,
            requested_store_id=requested_store_id,
            persist=True,
        )
        if response.draft_created:
            return response.message
        if response.items or response.clarification_questions:
            return response.message

    if _should_parse_before_context(text):
        response = _draft_order_payload(
            db,
            text=text,
            user_id=user_id,
            requested_store_id=requested_store_id,
            persist=True,
        )
        if response.draft_created:
            return response.message
        if response.items or response.clarification_questions:
            return response.message

    merged_text = _merge_context_text(context_text, text) if _should_extend_order_context(text) else None
    if merged_text:
        response = _draft_order_payload(
            db,
            text=merged_text,
            user_id=user_id,
            requested_store_id=requested_store_id,
            persist=True,
        )
        if response.draft_created:
            return response.message
        if response.items or response.clarification_questions:
            return response.message

    if not (_looks_like_product_fragment(text) or _looks_like_order_request(text)):
        return None

    response = _draft_order_payload(
        db,
        text=text,
        user_id=user_id,
        requested_store_id=requested_store_id,
        persist=True,
    )

    if response.draft_created:
        return response.message
    if response.items or response.clarification_questions:
        return response.message
    return None


@router.post("/draft-order", response_model=NLPDraftOrderResponse, status_code=status.HTTP_201_CREATED)
async def draft_order_from_text(body: NLPParseOrderRequest, user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    requested_store_id = body.store_id or body.customer_id
    return _draft_order_payload(
        db,
        text=body.text,
        user_id=user_id,
        requested_store_id=requested_store_id,
        persist=True,
    )


@router.post("/parse", response_model=NLPParseResponse)
async def parse_order_text(body: NLPParseRequest, user_id: str = Depends(get_current_user_id)):
    """Backward-compatible parser used by the mobile voice flow."""
    db = get_supabase_admin()
    structured = _parse_order_payload(
        db,
        text=body.text,
        user_id=user_id,
        requested_store_id=body.store_id,
        persist=True,
        require_store=False,
    )

    parsed_products: list[NLPProductMatch] = []
    for item in structured.items:
        candidate = item.sku_candidates[0] if item.sku_candidates else None
        if not candidate:
            continue
        price = float(candidate.price or 0)
        parsed_products.append(NLPProductMatch(
            name=candidate.product or item.producto_normalizado or "Producto",
            product_id=candidate.product_id,
            quantity=item.cantidad,
            unit_price=price,
            subtotal=price * item.cantidad,
        ))

    total = sum(item.subtotal for item in parsed_products)
    return NLPParseResponse(
        products=parsed_products,
        delivery_date=structured.fecha_entrega,
        total=total,
        requires_confirmation=True,
        message=structured.message,
    )


@router.post("/validate-extraction", response_model=NLPValidationResponse)
async def validate_extraction(body: NLPValidateExtractionRequest, user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    issues: list[NLPValidationIssue] = []

    if body.store_id:
        store = db.table("stores").select("id").eq("id", body.store_id).eq("user_id", user_id).execute()
        if not store.data:
            issues.append(NLPValidationIssue(type="customer", message="La tienda no existe o no pertenece al usuario."))
    else:
        issues.append(NLPValidationIssue(type="customer", message="Falta asociar una tienda/cliente al pedido."))

    today = date.today()
    max_date = today + timedelta(days=7)
    if not body.delivery_date:
        issues.append(NLPValidationIssue(type="date", message="Falta fecha de entrega."))
    elif body.delivery_date < today or body.delivery_date > max_date:
        issues.append(NLPValidationIssue(
            type="date",
            message=f"La fecha de entrega debe estar entre {today.isoformat()} y {max_date.isoformat()}.",
        ))

    for item in body.items:
        if item.quantity <= 0:
            issues.append(NLPValidationIssue(
                type="quantity",
                product_id=item.product_id,
                message="La cantidad debe ser mayor a cero.",
            ))
            continue

        product = db.table("products").select("*").eq("id", item.product_id).eq("active", True).execute()
        if not product.data:
            issues.append(NLPValidationIssue(
                type="product",
                product_id=item.product_id,
                message=f"Producto {item.product_id} no encontrado o inactivo.",
            ))
            continue

        row = product.data[0]
        if int(row.get("stock") or 0) < item.quantity:
            issues.append(NLPValidationIssue(
                type="stock",
                product_id=item.product_id,
                message=f"No hay stock suficiente de {row.get('name')}. Disponible: {row.get('stock')}.",
            ))

    validation_status = "valid" if not issues else "requires_clarification"
    if any(issue.type == "stock" for issue in issues):
        validation_status = "invalid"

    return NLPValidationResponse(
        validation_status=validation_status,
        requires_clarification=bool(issues),
        issues=issues,
    )


@router.post("/correct", status_code=status.HTTP_201_CREATED)
async def correct_extraction(body: NLPCorrectionRequest, user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    interaction = db.table("nlp_interactions").select("id").eq("id", body.interaction_id).execute()
    if not interaction.data:
        raise HTTPException(status_code=404, detail="Interaccion NLP no encontrada")

    result = db.table("nlp_corrections").insert({
        "interaction_id": body.interaction_id,
        "original_extraction": body.original_extraction,
        "corrected_extraction": body.corrected_extraction,
        "correction_reason": body.correction_reason,
        "corrected_by": user_id,
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="No se pudo guardar la correccion")
    return result.data[0]


@router.get("/interactions")
async def list_interactions(
    limit: int = Query(default=50, ge=1, le=200),
    _user_id: str = Depends(get_current_user_id),
):
    db = get_supabase_admin()
    return (
        db.table("nlp_interactions")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
        .data
        or []
    )


@router.get("/metrics")
async def nlp_metrics(_user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    interactions = (
        db.table("nlp_interactions")
        .select("confidence_score, validation_status, requires_human_review")
        .execute()
        .data
        or []
    )
    total = len(interactions)
    if not total:
        return {
            "total_interactions": 0,
            "average_confidence": 0,
            "requires_human_review_rate": 0,
            "by_status": {},
        }

    by_status: dict[str, int] = {}
    review_count = 0
    confidence_sum = 0.0
    for item in interactions:
        status_name = item.get("validation_status") or "unknown"
        by_status[status_name] = by_status.get(status_name, 0) + 1
        if item.get("requires_human_review"):
            review_count += 1
        confidence_sum += float(item.get("confidence_score") or 0)

    return {
        "total_interactions": total,
        "average_confidence": round(confidence_sum / total, 2),
        "requires_human_review_rate": round(review_count / total, 2),
        "by_status": by_status,
    }


@router.get("/llm-status", tags=["nlp"])
async def llm_status():
    """Return the operational status of the Ollama LLM fallback service.

    Useful for monitoring dashboards and deployment verification.
    """
    from app.services.llm import check_ollama_status  # local import to avoid circular deps
    return await check_ollama_status()
