import sys
from pathlib import Path
from typing import Any
import re

sys.path.append(str(Path("/home/jairomgr/Proyectos/expo/Emergentes_Preventista/backend")))

from app.config import get_supabase_admin
from app.routes.nlp import (
    _clean_segment,
    _product_signal_text,
    _product_family,
    _canonical_presentation,
    _normalize,
    PRESENTATION_RE,
    TYPO_REPLACEMENTS
)
from rapidfuzz import fuzz

db = get_supabase_admin()
products = db.table("products").select("*").eq("active", True).execute().data
db_aliases = db.table("product_aliases").select("*").eq("is_active", True).execute().data

def _spelling_variants_modified(value: str | None) -> set[str]:
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

    # Plural to singular spelling variants
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

def _unit_variants_modified(value: str | None) -> set[str]:
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

def _match_variants_modified(value: str | None) -> set[str]:
    variants = set()
    for spelling_variant in _spelling_variants_modified(value):
        variants.update(_unit_variants_modified(spelling_variant))
    return variants

def _product_aliases_modified(product: dict[str, Any], aliases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    product_name = product.get("name", "")
    generated: list[dict[str, Any]] = []

    for alias in _unit_variants_modified(product_name):
        generated.append({"alias": alias, "weight": 1.0, "type": "official"})

    base_name = PRESENTATION_RE.sub("", _normalize(product_name)).strip()
    if base_name:
        generated.append({"alias": base_name, "weight": 0.72, "type": "product_only"})
        generated.append({"alias": re.sub(r"\bcola\b", "", base_name).strip(), "weight": 0.68, "type": "short_name"})

    # Specific rule for Agua Cielo
    presentation = _canonical_presentation(product_name)
    if "agua cielo" in base_name and presentation:
        for v in _unit_variants_modified(f"agua {presentation}"):
            generated.append({"alias": v, "weight": 1.0, "type": "short_name_pres"})
        for v in _unit_variants_modified(f"cielo {presentation}"):
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

def _score_alias_modified(clean_item: str, alias: str, weight: float) -> float:
    score = 0.0
    for item_variant in _match_variants_modified(clean_item):
        if alias and (alias in item_variant or item_variant in alias):
            score = max(score, 100.0)
        score = max(
            score,
            float(fuzz.WRatio(item_variant, alias)),
            float(fuzz.token_set_ratio(item_variant, alias)),
        )
    return min(100.0, score * weight)

def _sku_candidates_modified(clean_item: str, products: list[dict[str, Any]], aliases: list[dict[str, Any]]) -> list[Any]:
    candidates = {}
    for product in products:
        best_score = 0.0
        for alias in _product_aliases_modified(product, aliases):
            best_score = max(best_score, _score_alias_modified(clean_item, alias["alias"], alias["weight"]))
        if best_score < 45:
            continue
        product_id = product.get("id")
        candidates[str(product_id)] = (product.get("name"), best_score)
    return sorted(candidates.values(), key=lambda x: x[1], reverse=True)[:3]

# Test
clean_item = "aguas de 500" # quantity removed from "2 aguas de 500"
print("Clean item:", clean_item)
candidates = _sku_candidates_modified(clean_item, products, db_aliases)
print("Candidates:")
for name, score in candidates:
    print(f"  {name}: {score}")
