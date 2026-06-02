import sys
sys.path.append('backend')
from app.routes.nlp import _best_product, _parse_quantity, _normalize, _extract_delivery_date, SPLIT_RE
from app.local_db import get_local_client

db = get_local_client()
products = db.table("products").select("*").eq("active", True).execute().data

test_cases = [
    "quiero agua",
    "2",
    "10",
    "quiero 8 aguas",
    "quiero 8 aguas 1l",
    "quiero 8 aguas 1l para mañana",
    "kiero 8 aguas 1l pa mañna",
    "quiero 3 aguas y 4 big cola",
    "quiero 3 aguas 1l y 4 big cola 2l",
    "quiero 3 aguas 1l y 4 big cola 2l para mañana",
    "quiero 3 aguas y 4 bil cloas",
    "quiero 4 bil cloas 2l",
    "quiero coca cola",
    "quiero 20 sporade",
    "quiero 10 sporade 1l para pasado mañana",
    "quiero volt",
    "quiero 1000 aguas 500ml",
    "agua cielo de medio litro",
    "agua cielo de un litro",
    "quiero 3 aguas 1l para el 31 de enero",
    "quiero 3 aguas 1l para 31/01",
    "quiero 3 aguas 1l, 4 big cola 2l, 5 sporade 500ml para mañana",
    "kiero 3 aguas 1l, 4 bil cloas 2l y 5 sporades pa mañna"
]

print("--- NLP TEST ---")
for tc in test_cases:
    print(f"\nInput: '{tc}'")
    segments = [part for part in SPLIT_RE.split(_normalize(tc)) if part]
    if not segments and tc:
        segments = [_normalize(tc)]
    print(f"Segments: {segments}")
    for seg in segments:
        prod, score = _best_product(seg, products)
        qty = _parse_quantity(seg)
        print(f"  Segment: '{seg}' -> Match: '{prod['name'] if prod else None}' (Score: {score}), Qty: {qty}")
    date = _extract_delivery_date(tc)
    print(f"  Delivery Date: {date}")
