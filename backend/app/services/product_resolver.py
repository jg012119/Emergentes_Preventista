"""Product resolver service.

Resolves a product name detected by the LLM against the real DB catalog
using a priority-based strategy that eliminates ambiguous substring matching.

Resolution priority:
  1. Exact product ID match
  2. Exact SKU / official name match (case-insensitive, normalized)
  3. Exact alias match (from product_aliases table)
  4. Brand + presentation combined match
  5. RapidFuzz similarity match (last resort, threshold ≥ 70)
  6. Ambiguous → return status=ambiguous with options list
  7. Not found → return status=not_found
"""

from __future__ import annotations

import unicodedata
import re
from dataclasses import dataclass, field
from typing import Any

from rapidfuzz import fuzz

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FUZZY_MIN_SCORE = 70        # Minimum score to consider a fuzzy match
FUZZY_AUTO_ACCEPT = 88      # Above this: accept without clarification
AMBIGUOUS_GAP = 6           # If top-2 scores differ by less than this → ambiguous

# Presentation qualitative → canonical mapping
_PRESENTATION_MAP: dict[str, str] = {
    # Volt specific
    "volt chico": "300ml",
    "voltcito": "300ml",
    "volt grande": "500ml",
    "volt mediano": "500ml",
    
    # Coca-Cola specific
    "coca chica": "500ml",
    "coca chiquita": "500ml",
    "coca personal": "500ml",
    "coquita": "500ml",
    "coca grande": "2L",
    "coca familiar": "2L",
    
    # Agua Cielo specific
    "agua chica": "500ml",
    "agua chiquita": "500ml",
    "agua personal": "500ml",
    "agua grande": "2.5L",
    "agua familiar": "2.5L",

    # General qualitative terms
    "chico": "500ml",
    "chica": "500ml",
    "chika": "500ml",
    "chiquito": "500ml",
    "chiquita": "500ml",
    "personal": "500ml",
    "pequeño": "500ml",
    "pequeña": "500ml",
    "medio litro": "500ml",
    "un litro y medio": "1.5L",
    "litro y medio": "1.5L",
    "un litro": "1L",
    "litro": "1L",
    "mediano": "1L",
    "grande": "2L",
    "familiar": "2L",
    "dos litros": "2L",
    "super grande": "3L",
    "tres litros": "3L",
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ResolvedProduct:
    """Result of resolving one LLM-detected product against the DB catalog."""
    status: str                          # matched | ambiguous | not_found | missing_presentation
    product_id: str | None = None
    product_name: str | None = None
    product_price: float | None = None
    quantity: int = 1
    confidence: float = 0.0
    match_reason: str = ""               # alias | name | fuzzy | brand+presentation
    options: list[dict[str, Any]] = field(default_factory=list)
    clarification_question: str | None = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize(value: str | None) -> str:
    """Lowercase, strip accents, collapse whitespace."""
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9.]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _canonical_presentation(raw: str | None) -> str | None:
    """Normalize a presentation string to canonical form (e.g. '500ml', '2L')."""
    if not raw:
        return None
    normalized = _normalize(raw)

    # Check qualitative map first on word boundaries
    for key in sorted(_PRESENTATION_MAP.keys(), key=len, reverse=True):
        if re.search(rf"\b{re.escape(key)}\b", normalized):
            return _PRESENTATION_MAP[key]

    # Numeric: 500ml / 2L / 1.5L
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(ml|l|lt|lts|litros?)", normalized)
    if m:
        amount = m.group(1).replace(",", ".")
        unit = m.group(2)
        if unit.startswith("m"):
            return f"{int(float(amount))}ml"
        amount_str = str(int(float(amount))) if float(amount) == int(float(amount)) else amount
        return f"{amount_str}L"

    return None


def _product_presentation(product_name: str) -> str | None:
    """Extract presentation from a canonical product name like 'Agua Cielo 500ml'."""
    m = re.search(r"(\d+(?:\.\d+)?)\s*(ml|L)", product_name, re.IGNORECASE)
    if m:
        return m.group(0)
    return None


def _presentations_match(requested: str | None, product_name: str) -> bool:
    """Check if a requested presentation matches the product's presentation."""
    if not requested:
        return True  # No presentation specified — any presentation is acceptable
    canonical_req = _canonical_presentation(requested)
    canonical_prod = _canonical_presentation(_product_presentation(product_name))
    if not canonical_req or not canonical_prod:
        return True
    return canonical_req.lower() == canonical_prod.lower()


def _build_options(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build a list of option dicts for a clarification question."""
    return [
        {
            "product_id": p["id"],
            "name": p["name"],
            "price": round(float(p.get("price") or 0), 2),
        }
        for p in candidates
    ]


def _clarification_question(product_name: str, options: list[dict[str, Any]]) -> str:
    names = ", ".join(o["name"] for o in options)
    return f"¿Cuál '{product_name}' quieres? Tenemos: {names}"


# ---------------------------------------------------------------------------
# Main resolver
# ---------------------------------------------------------------------------

def resolve_product(
    detected_name: str,
    quantity: int,
    presentation: str | None,
    catalog: list[dict[str, Any]],
    aliases: list[dict[str, Any]] | None = None,
) -> ResolvedProduct:
    """Resolve one LLM-detected product against the catalog.

    Args:
        detected_name: The 'nombre_detectado' from the LLM (e.g. "agua cielo", "voltcito")
        quantity: Quantity from the LLM
        presentation: Presentation from LLM (e.g. "500ml", "chica", "familiar") or None
        catalog: List of product dicts from DB (must have 'id', 'name', 'price')
        aliases: Optional list of alias dicts from DB (product_id, normalized_alias, alias_text)

    Returns:
        ResolvedProduct with status in: matched | ambiguous | not_found | missing_presentation
    """
    norm_detected = _normalize(detected_name)
    canonical_pres = _canonical_presentation(presentation)

    # ── Priority 1: Exact product name match (case-insensitive, normalized) ──
    for product in catalog:
        if _normalize(product.get("name", "")) == norm_detected:
            return ResolvedProduct(
                status="matched",
                product_id=product["id"],
                product_name=product["name"],
                product_price=float(product.get("price") or 0),
                quantity=quantity,
                confidence=1.0,
                match_reason="name_exact",
            )

    # ── Priority 2: Exact alias match ──
    if aliases:
        alias_matches: list[dict[str, Any]] = []
        for alias_row in aliases:
            norm_alias = _normalize(alias_row.get("normalized_alias") or alias_row.get("alias_text", ""))
            if norm_alias == norm_detected:
                # Find the matching product in catalog
                prod = next((p for p in catalog if p["id"] == alias_row.get("product_id")), None)
                if prod:
                    alias_matches.append({**prod, "_weight": float(alias_row.get("confidence_weight", 1.0))})

        if alias_matches:
            if canonical_pres:
                # Filter by presentation first
                pres_matches = [p for p in alias_matches if _presentations_match(canonical_pres, p["name"])]
                if len(pres_matches) == 1:
                    p = pres_matches[0]
                    return ResolvedProduct(
                        status="matched",
                        product_id=p["id"],
                        product_name=p["name"],
                        product_price=float(p.get("price") or 0),
                        quantity=quantity,
                        confidence=p["_weight"],
                        match_reason="alias_exact",
                    )
                if len(pres_matches) > 1:
                    # Multiple matches with presentation — ambiguous
                    options = _build_options(pres_matches)
                    return ResolvedProduct(
                        status="ambiguous",
                        quantity=quantity,
                        confidence=0.5,
                        match_reason="alias_ambiguous",
                        options=options,
                        clarification_question=_clarification_question(detected_name, options),
                    )
            else:
                # No presentation specified
                if len(alias_matches) == 1:
                    p = alias_matches[0]
                    return ResolvedProduct(
                        status="matched",
                        product_id=p["id"],
                        product_name=p["name"],
                        product_price=float(p.get("price") or 0),
                        quantity=quantity,
                        confidence=p["_weight"],
                        match_reason="alias_exact",
                    )
                # Multiple products share this alias — ask for clarification
                options = _build_options(alias_matches)
                return ResolvedProduct(
                    status="ambiguous",
                    quantity=quantity,
                    confidence=0.5,
                    match_reason="alias_ambiguous",
                    options=options,
                    clarification_question=_clarification_question(detected_name, options),
                )

    # ── Priority 3: Partial name match + presentation filter ──
    if canonical_pres:
        pres_candidates = [
            p for p in catalog
            if norm_detected in _normalize(p.get("name", ""))
            and _presentations_match(canonical_pres, p["name"])
        ]
        if len(pres_candidates) == 1:
            p = pres_candidates[0]
            return ResolvedProduct(
                status="matched",
                product_id=p["id"],
                product_name=p["name"],
                product_price=float(p.get("price") or 0),
                quantity=quantity,
                confidence=0.85,
                match_reason="name+presentation",
            )

    # ── Priority 4: Brand match — if detected_name matches a brand prefix ──
    brand_candidates = [
        p for p in catalog
        if _normalize(p.get("name", "")).startswith(norm_detected)
    ]
    if brand_candidates:
        if canonical_pres:
            pres_filtered = [p for p in brand_candidates if _presentations_match(canonical_pres, p["name"])]
            if len(pres_filtered) == 1:
                p = pres_filtered[0]
                return ResolvedProduct(
                    status="matched",
                    product_id=p["id"],
                    product_name=p["name"],
                    product_price=float(p.get("price") or 0),
                    quantity=quantity,
                    confidence=0.90,
                    match_reason="brand+presentation",
                )

        # Multiple brand matches without disambiguating presentation
        if len(brand_candidates) == 1:
            p = brand_candidates[0]
            return ResolvedProduct(
                status="matched",
                product_id=p["id"],
                product_name=p["name"],
                product_price=float(p.get("price") or 0),
                quantity=quantity,
                confidence=0.80,
                match_reason="brand_prefix",
            )

        options = _build_options(brand_candidates)
        return ResolvedProduct(
            status="ambiguous",
            quantity=quantity,
            confidence=0.5,
            match_reason="brand_ambiguous",
            options=options,
            clarification_question=_clarification_question(detected_name, options),
        )

    # ── Priority 5: RapidFuzz similarity ──
    scored: list[tuple[float, dict[str, Any]]] = []
    for product in catalog:
        norm_name = _normalize(product.get("name", ""))
        score = fuzz.token_set_ratio(norm_detected, norm_name)
        if score >= FUZZY_MIN_SCORE:
            scored.append((score, product))

    # Also score against aliases if available
    if aliases:
        for alias_row in aliases:
            norm_alias = _normalize(alias_row.get("normalized_alias") or alias_row.get("alias_text", ""))
            score = fuzz.token_set_ratio(norm_detected, norm_alias)
            if score >= FUZZY_MIN_SCORE:
                prod = next((p for p in catalog if p["id"] == alias_row.get("product_id")), None)
                if prod:
                    # Avoid duplicates — keep highest score for each product
                    existing = next((s for s in scored if s[1]["id"] == prod["id"]), None)
                    if existing:
                        if score > existing[0]:
                            scored = [(s[0], s[1]) for s in scored if s[1]["id"] != prod["id"]]
                            scored.append((score, prod))
                    else:
                        scored.append((score, prod))

    if not scored:
        return ResolvedProduct(
            status="not_found",
            quantity=quantity,
            confidence=0.0,
            match_reason="no_match",
        )

    # Sort by score descending
    scored.sort(key=lambda x: -x[0])

    # Filter by presentation if available
    if canonical_pres:
        pres_scored = [(sc, p) for sc, p in scored if _presentations_match(canonical_pres, p["name"])]
        if pres_scored:
            scored = pres_scored

    best_score, best_product = scored[0]

    # Check for ambiguity: if second candidate is too close
    if len(scored) >= 2:
        second_score = scored[1][0]
        if best_score - second_score < AMBIGUOUS_GAP and best_score < FUZZY_AUTO_ACCEPT:
            options = _build_options([p for _, p in scored[:4]])
            return ResolvedProduct(
                status="ambiguous",
                quantity=quantity,
                confidence=best_score / 100,
                match_reason="fuzzy_ambiguous",
                options=options,
                clarification_question=_clarification_question(detected_name, options),
            )

    return ResolvedProduct(
        status="matched",
        product_id=best_product["id"],
        product_name=best_product["name"],
        product_price=float(best_product.get("price") or 0),
        quantity=quantity,
        confidence=best_score / 100,
        match_reason="fuzzy",
    )


def resolve_all_products(
    llm_products: list[Any],  # list of LlamaProduct
    catalog: list[dict[str, Any]],
    aliases: list[dict[str, Any]] | None = None,
) -> list[ResolvedProduct]:
    """Resolve a list of LlamaProduct objects against the catalog.

    Args:
        llm_products: list of LlamaProduct from ask_llm()
        catalog: full list of products from DB
        aliases: optional list of aliases from DB

    Returns:
        list of ResolvedProduct, one per LlamaProduct
    """
    results: list[ResolvedProduct] = []
    for item in llm_products:
        resolved = resolve_product(
            detected_name=item.nombre_detectado,
            quantity=item.cantidad,
            presentation=item.presentacion,
            catalog=catalog,
            aliases=aliases,
        )
        results.append(resolved)
    return results
