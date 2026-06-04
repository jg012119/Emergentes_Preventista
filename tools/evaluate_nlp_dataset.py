#!/usr/bin/env python3
"""Evaluate the order NLP parser against a curated local dataset."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
DEFAULT_DATASET = BACKEND / "app" / "nlp_dataset" / "cochabamba_cercado_orders.json"

sys.path.insert(0, str(BACKEND))


@dataclass
class Counters:
    total_cases: int = 0
    total_items: int = 0
    product_expected_items: int = 0
    presentation_expected_items: int = 0
    quantity_expected_items: int = 0
    unit_expected_items: int = 0
    matched_items: int = 0
    product_hits: int = 0
    presentation_hits: int = 0
    quantity_hits: int = 0
    unit_hits: int = 0
    date_hits: int = 0
    expected_dates: int = 0
    expected_clarification_cases: int = 0
    clarification_hits: int = 0


def _load_dataset(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError("Dataset root must be a JSON array")
    return data


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower()


def _expected_date(case: dict[str, Any]) -> str | None:
    if "delivery_date" in case:
        return str(case["delivery_date"])
    if "delivery_offset_days" in case:
        return (date.today() + timedelta(days=int(case["delivery_offset_days"]))).isoformat()
    return None


def _load_backend(force_local: bool):
    if force_local:
        os.environ["SUPABASE_URL"] = ""
        os.environ["SUPABASE_KEY"] = ""
        os.environ["SUPABASE_SERVICE_KEY"] = ""

    from app.config import get_supabase_admin
    from app.routes.nlp import _parse_order_payload

    return get_supabase_admin, _parse_order_payload


def _evaluate_case(db, parse_order_payload, case: dict[str, Any], counters: Counters) -> dict[str, Any]:
    result = parse_order_payload(
        db,
        text=case["text"],
        user_id="nlp-evaluation",
        requested_store_id=None,
        persist=False,
        require_store=bool(case.get("require_store", False)),
    )

    expected_items = case.get("items", [])
    actual_items = result.items
    failures: list[str] = []

    counters.total_cases += 1
    counters.total_items += len(expected_items)

    for index, expected in enumerate(expected_items):
        if index >= len(actual_items):
            failures.append(f"item {index + 1}: missing; expected {expected}")
            continue

        actual = actual_items[index]
        counters.matched_items += 1

        if "product" in expected:
            counters.product_expected_items += 1
            if _normalize(actual.producto_normalizado) == _normalize(expected.get("product")):
                counters.product_hits += 1
            else:
                failures.append(
                    f"item {index + 1}: product expected {expected.get('product')!r}, "
                    f"got {actual.producto_normalizado!r}"
                )

        if "presentation" in expected:
            counters.presentation_expected_items += 1
            if _normalize(actual.presentacion) == _normalize(expected.get("presentation")):
                counters.presentation_hits += 1
            else:
                failures.append(
                    f"item {index + 1}: presentation expected {expected.get('presentation')!r}, "
                    f"got {actual.presentacion!r}"
                )

        if "quantity" in expected:
            counters.quantity_expected_items += 1
            if int(actual.cantidad) == int(expected.get("quantity", 0)):
                counters.quantity_hits += 1
            else:
                failures.append(
                    f"item {index + 1}: quantity expected {expected.get('quantity')!r}, "
                    f"got {actual.cantidad!r}"
                )

        if "unit" in expected:
            counters.unit_expected_items += 1
            if _normalize(actual.unidad) == _normalize(expected.get("unit")):
                counters.unit_hits += 1
            else:
                failures.append(
                    f"item {index + 1}: unit expected {expected.get('unit')!r}, "
                    f"got {actual.unidad!r}"
                )

    if len(actual_items) > len(expected_items) and not case.get("allow_extra_items"):
        failures.append(f"extra items: expected {len(expected_items)}, got {len(actual_items)}")

    expected_unresolved_items = case.get("expected_unresolved_items") or []
    for expected in expected_unresolved_items:
        expected_raw = _normalize(expected.get("raw_text"))
        matching_items = [
            item
            for item in actual_items
            if expected_raw and expected_raw in _normalize(item.raw_text)
        ]
        if not matching_items:
            failures.append(f"unresolved item expected {expected.get('raw_text')!r}, got {[item.raw_text for item in actual_items]!r}")
            continue
        actual = matching_items[0]
        if actual.producto_normalizado or actual.product_id or actual.sku_id:
            failures.append(
                f"unresolved item {expected.get('raw_text')!r}: expected no SKU/product, "
                f"got {actual.producto_normalizado!r}"
            )

    expected_clarification_types = case.get("expected_clarification_types") or []
    if expected_clarification_types:
        counters.expected_clarification_cases += 1
        actual_types = [question.type for question in result.clarification_questions]
        missing_types = [
            expected_type
            for expected_type in expected_clarification_types
            if expected_type not in actual_types
        ]
        if missing_types:
            failures.append(f"clarification types expected {expected_clarification_types!r}, got {actual_types!r}")
        else:
            counters.clarification_hits += 1

    expected_date = _expected_date(case)
    if expected_date:
        counters.expected_dates += 1
        if result.fecha_entrega == expected_date:
            counters.date_hits += 1
        else:
            failures.append(f"date expected {expected_date!r}, got {result.fecha_entrega!r}")

    return {
        "id": case.get("id"),
        "text": case.get("text"),
        "passed": not failures,
        "failures": failures,
        "validation_status": result.validation_status,
        "requires_clarification": result.requires_clarification,
        "clarification_questions": [question.model_dump() for question in result.clarification_questions],
        "actual_items": [item.model_dump() for item in actual_items],
        "actual_date": result.fecha_entrega,
    }


def _rate(hit: int, total: int) -> float:
    return round(hit / total, 4) if total else 1.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate NLP parser with the Cochabamba/Cercado dataset.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--min-product-accuracy", type=float, default=0.85)
    parser.add_argument("--min-quantity-accuracy", type=float, default=0.95)
    parser.add_argument("--min-presentation-accuracy", type=float, default=0.80)
    parser.add_argument("--min-clarification-accuracy", type=float, default=1.00)
    parser.add_argument("--epochs", type=int, default=1, help="Repeat the deterministic evaluation N times.")
    parser.add_argument("--local", action="store_true", help="Force the local SQLite fallback instead of Supabase.")
    parser.add_argument("--json", action="store_true", help="Print full JSON results.")
    args = parser.parse_args()

    get_supabase_admin, parse_order_payload = _load_backend(args.local)
    dataset = _load_dataset(args.dataset)
    db = get_supabase_admin()
    counters = Counters()
    results = []
    for epoch in range(1, max(1, args.epochs) + 1):
        for case in dataset:
            result = _evaluate_case(db, parse_order_payload, case, counters)
            result["epoch"] = epoch
            results.append(result)

    summary = {
        "dataset": str(args.dataset),
        "epochs": max(1, args.epochs),
        "cases": counters.total_cases,
        "items": counters.total_items,
        "product_accuracy": _rate(counters.product_hits, counters.product_expected_items),
        "presentation_accuracy": _rate(counters.presentation_hits, counters.presentation_expected_items),
        "quantity_accuracy": _rate(counters.quantity_hits, counters.quantity_expected_items),
        "date_accuracy": _rate(counters.date_hits, counters.expected_dates),
        "clarification_accuracy": _rate(counters.clarification_hits, counters.expected_clarification_cases),
        "failed_cases": [item for item in results if not item["passed"]],
    }

    if args.json:
        print(json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2))
    else:
        print(f"Dataset: {summary['dataset']}")
        print(f"Epochs: {summary['epochs']}")
        print(f"Cases: {summary['cases']} | Items: {summary['items']}")
        print(f"Product accuracy: {summary['product_accuracy']:.2%}")
        print(f"Presentation accuracy: {summary['presentation_accuracy']:.2%}")
        print(f"Quantity accuracy: {summary['quantity_accuracy']:.2%}")
        print(f"Date accuracy: {summary['date_accuracy']:.2%}")
        print(f"Clarification accuracy: {summary['clarification_accuracy']:.2%}")
        if summary["failed_cases"]:
            print("\nFailed cases:")
            for case in summary["failed_cases"]:
                print(f"- epoch {case['epoch']} | {case['id']}: {case['text']}")
                for failure in case["failures"]:
                    print(f"  * {failure}")

    if (
        summary["product_accuracy"] < args.min_product_accuracy
        or summary["quantity_accuracy"] < args.min_quantity_accuracy
        or summary["presentation_accuracy"] < args.min_presentation_accuracy
        or summary["clarification_accuracy"] < args.min_clarification_accuracy
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
