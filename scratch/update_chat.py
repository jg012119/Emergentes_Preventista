import re

file_path = "app/routes/chat.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# We want to replace the body of _build_chat_reply with the new intent-based logic.
# It starts at: def _build_chat_reply(db, user_id: str, body: ChatMessageCreate) -> str | None:
# and ends at: @router.post("/message"

start_idx = content.find("def _build_chat_reply(db, user_id: str, body: ChatMessageCreate) -> str | None:")
end_idx = content.find("@router.post(\"/message\"", start_idx)

original_func = content[start_idx:end_idx]

new_func = """def _build_chat_reply(db, user_id: str, body: ChatMessageCreate) -> str | None:
    \"\"\"Generate a chat reply based on user message.
    Handles product queries, missing presentation, quantity, stock checks,
    date prompts, order status, and menu requests.
    Supports multiple items in a single message separated by 'y', ',', '+', etc.
    \"\"\"
    if _is_structured_order_message(body.message):
        return None

    text = _normalize_text(body.message)
    status_filter = _find_status_filter(text)

    # ── Generic intents (check FIRST, before product matching) ──
    if "menu" in text or "catalogo" in text or "productos" in text:
        return _build_product_menu(db, user_id)

    if "estado" in text or "seguimiento" in text or "como va" in text:
        return _order_status_message(db, user_id, body.order_id)

    if ("pedido" in text or "pedidos" in text or "ordenes" in text or "lista" in text) and not re.search(r"\d", text):
        return _list_orders_message(db, user_id, status_filter)

    if status_filter and not re.search(r"\d", text):
        return _list_orders_message(db, user_id, status_filter)

    # Import NLP helpers
    from app.routes.nlp import _best_product, _parse_quantity, _normalize, SPLIT_RE, _extract_delivery_date

    # ── Helper: extract delivery date with multiple fallbacks ──
    def _get_delivery(raw_text: str) -> str | None:
        delivery = _extract_delivery_date(raw_text)
        if delivery:
            return delivery
        # Fallback: "para <date text>"
        m = re.search(r"para\s+(.+)", raw_text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            # Remove trailing product-like words that might have been captured
            candidate = re.sub(r"\s+(y|mas|tambien)\s+.*$", "", candidate, flags=re.IGNORECASE).strip()
            if candidate:
                return candidate
        # Fallback: bare "3 de junio" pattern
        m2 = re.search(r"\\b(\d{1,2}\s*de\s+\w+)\\b", raw_text, re.IGNORECASE)
        if m2:
            return m2.group(1).strip()
        return None

    # ── Helper: detect location (Cochabamba zones) ──
    def _get_location(raw_text: str) -> str | None:
        \"\"\"Extract Cochabamba delivery zones for notes.\"\"\"
        m = re.search(
            r"(?:por|en|a|zona)\s+(?:mi tienda de\s+|la\s+|el\s+)?(cala cala|aroma|jaihuayco|la cancha|cancha|valle hermoso|zona norte|zona sur|ayacucho|queru queru|muyurina|cochabamba|cercado|centro|pacata)",
            raw_text,
            re.IGNORECASE,
        )
        if m:
            return f"Entrega en zona {m.group(1).title()}, Cochabamba Cercado"
        return None

    # ── Helper: detect size token WITHOUT matching bare numbers ──
    from app.routes.nlp import SIZE_ALIASES
    SIZE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(ml|l|litros?)\\b", re.IGNORECASE)
    TEXT_SIZE_RE = re.compile(
        r"\\b(medio\s+litro|litro\s+y\s+medio|cuarto\s+de\s+litro|medio|cuarto|mediano|grande|pequeño|chico|familiar|personal|500|600|750|330|250|400|450|1\.5|2\.5|3\.3|2\.25)\\b",
        re.IGNORECASE,
    )

    def _detect_size(seg: str) -> str | None:
        # First try numeric: "500ml", "1l", "1.5l"
        m = SIZE_RE.search(seg)
        if m:
            return m.group(0).lower().strip()
        # Then try text-based: "medio litro" -> "500ml"
        m2 = TEXT_SIZE_RE.search(seg)
        if m2:
            key = re.sub(r"\s+", " ", m2.group(0).lower().strip())
            return SIZE_ALIASES.get(key)
        return None

    # ── Helper: detect explicit quantity (only bare numbers NOT attached to a unit) ──
    def _has_explicit_qty(seg: str) -> bool:
        \"\"\"Return True if there is a number that is NOT part of a size token.\"\"\"
        cleaned = SIZE_RE.sub("", seg)  # remove size tokens like '1l', '500ml'
        cleaned = re.sub(r"\\b\d{1,2}\s*de\s+\w+", "", cleaned, flags=re.IGNORECASE)  # remove date patterns
        return bool(re.search(r"\\b\d+\\b", cleaned))

    # ── NLU Intents Detection ──
    intent = "crear_pedido"
    
    if re.search(r"^(?:cancela|anula|ya no quiero|olvidalo|cancela el pedido)", body.message, re.IGNORECASE):
        intent = "cancelar_pedido"
    elif re.search(r"^(?:confirma|esta bien|mandalo|listo|ok|perfecto|asi esta bien|mandalo nomas)", body.message, re.IGNORECASE):
        intent = "confirmar_pedido"
    elif re.search(r"^(?:quita|elimina|saca|remueve|no me mandes|ya no me mandes)\b", body.message, re.IGNORECASE):
        intent = "quitar_producto"
    elif re.search(r"^(?:mejor para el|cambia la fecha|cambia a|que sea el)\b", body.message, re.IGNORECASE):
        intent = "cambiar_fecha"

    # Handle explicit DB Intents
    if intent == "cancelar_pedido":
        if not body.order_id:
            return "No tienes ningún pedido activo para cancelar."
        db.table("orders").update({"status": "cancelado"}).eq("id", body.order_id).execute()
        return "Pedido cancelado."

    if intent == "confirmar_pedido":
        if not body.order_id:
            return "No encuentro el pedido para confirmar."
        db.table("orders").update({"status": "pendiente"}).eq("id", body.order_id).execute()
        return "¡Pedido confirmado! Lo enviaremos pronto a AJE."

    if intent == "cambiar_fecha":
        if not body.order_id:
            return "No tienes un pedido activo para cambiar la fecha."
        delivery = _get_delivery(body.message)
        if delivery:
            db.table("orders").update({"delivery_date": delivery}).eq("id", body.order_id).execute()
            return f"Fecha de entrega actualizada a {delivery}."
        return "No pude entender la nueva fecha. Por favor indícala claramente."

    if intent == "quitar_producto":
        if not body.order_id:
            return "No tienes un pedido activo."
        all_products = db.table("products").select("*").eq("active", True).execute().data or []
        prod_to_remove, _ = _best_product(body.message, all_products)
        if prod_to_remove:
            # Query order items
            items = db.table("order_items").select("*").eq("order_id", body.order_id).execute().data
            for item in items:
                if item["product_id"] == prod_to_remove["id"]:
                    db.table("order_items").delete().eq("id", item["id"]).execute()
                    
                    # Recalculate total
                    new_items = db.table("order_items").select("*").eq("order_id", body.order_id).execute().data
                    new_total = sum(float(i["subtotal"]) for i in new_items)
                    db.table("orders").update({"total": new_total}).eq("id", body.order_id).execute()
                    
                    return f"He quitado {prod_to_remove.get('name')} del pedido."
            return f"No encontré {prod_to_remove.get('name')} en tu pedido actual."
        return "No entendí qué producto quieres quitar."

    # ── Conversation state: check previous bot message ──
    try:
        prev_msgs = (
            db.table("chat_messages")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(2)
            .execute()
            .data
        )
        if len(prev_msgs) >= 2 and prev_msgs[1].get("sender") == "empresa":
            last_bot = prev_msgs[1].get("message", "")
            last_bot_lower = last_bot.lower()

            # STATE: Awaiting presentation selection (user should answer with a number)
            if "presentación" in last_bot_lower:
                m = re.search(r"¿Qué presentación de (.+?) desea\?", last_bot)
                if m:
                    base_name = m.group(1).strip()
                    variants = (
                        db.table("products").select("*")
                        .eq("active", True).ilike("name", f"{base_name}%")
                        .execute().data
                    )
                    variants = sorted(variants, key=lambda p: p.get("name", ""))
                    try:
                        idx = int(body.message.strip()) - 1
                        if 0 <= idx < len(variants):
                            sel = variants[idx]
                            return f"¿Cuántas unidades desea de {sel.get('name')}?"
                    except ValueError:
                        pass

            # STATE: Awaiting quantity
            elif "cuántas unidades desea de" in last_bot_lower:
                try:
                    qty = int(body.message.strip())
                    m_qty = re.search(r"¿Cuántas unidades desea de (.+?)\?", last_bot)
                    if m_qty:
                        product_name = m_qty.group(1).strip()
                        prod = (
                            db.table("products").select("*")
                            .eq("active", True).eq("name", product_name)
                            .single().execute().data
                        )
                        if prod:
                            stock = prod.get("stock", 0)
                            if qty > stock:
                                return f"Lo siento, solo hay {stock} unidades de {product_name} disponibles. ¿Desea esa cantidad?"
                            
                            # Build the single item format to inject back into the order parsing flow
                            body.message = f"{qty} {product_name}"
                            # Let it fall through to the product parsing!
                    else:
                        return "Por favor, confirma el producto y la cantidad."
                except ValueError:
                    return "Por favor, ingresa una cantidad numérica válida."

            # STATE: Awaiting delivery date
            elif "fecha desea la entrega" in last_bot_lower:
                m_date = re.search(r"(\d+) unidades de (.+?)\?", last_bot)
                if m_date:
                    qty = int(m_date.group(1))
                    product_name = m_date.group(2).strip()
                    delivery = _get_delivery(body.message)
                    if delivery:
                        body.message = f"{qty} {product_name} para {delivery}"
                        # Let it fall through to product parsing!
                    else:
                        return "Por favor, indica la fecha de entrega (ej: mañana, 5 de junio)."
    except Exception:
        pass

    # ── Product parsing: split into segments and match each ──
    segments = [part for part in SPLIT_RE.split(_normalize(body.message)) if part]
    if not segments and body.message:
        segments = [_normalize(body.message)]

    # Global delivery date from the full message
    global_delivery = _get_delivery(body.message)
    # Cochabamba Zone
    zone_notes = _get_location(body.message)

    all_products = db.table("products").select("*").eq("active", True).execute().data or []
    order_items = []

    for seg in segments:
        # Find product
        product, _score = _best_product(seg, all_products)
        if not product:
            # Singular fallback: remove trailing 's'
            singular_seg = re.sub(r"\\b(\w+)s\\b", r"\\1", seg, flags=re.IGNORECASE)
            product, _score = _best_product(singular_seg, all_products)
        if not product:
            continue  # skip unrecognized segments

        # Size token
        size_token = _detect_size(seg)

        # If size found but doesn't match current product, find the right variant
        if size_token and size_token not in product.get("name", "").lower():
            base_name = re.sub(r"\s*\d+(?:\.\d+)?\s*(ml|l|litros?)$", "", product.get("name", ""), flags=re.IGNORECASE).strip()
            variants = [p for p in all_products if _normalize_text(p.get("name", "")).startswith(_normalize_text(base_name))]
            for v in variants:
                if size_token in v.get("name", "").lower():
                    product = v
                    break

        # Quantity
        qty = _parse_quantity(seg)
        explicit_qty = _has_explicit_qty(seg)

        # Per-segment delivery
        seg_delivery = _get_delivery(seg) or global_delivery

        order_items.append({
            "product": product,
            "size_token": size_token,
            "qty": qty,
            "explicit_qty": explicit_qty,
            "delivery": seg_delivery,
        })

    # ── No items matched ──
    if not order_items:
        return (
            "Puedo ayudarte con: menu de productos, estado del pedido, lista de pedidos, "
            "pedidos pendientes, confirmados, rechazados, en proceso o pagados."
        )

    # ── Process items: ask for missing info on the FIRST incomplete item ──
    for itm in order_items:
        product = itm["product"]
        size_token = itm["size_token"]
        qty = itm["qty"]
        explicit_qty = itm["explicit_qty"]

        # Missing presentation?
        if not size_token:
            base_name = re.sub(r"\s*\d+(?:\.\d+)?\s*(ml|l|litros?)$", "", product.get("name", ""), flags=re.IGNORECASE).strip()
            variants = [p for p in all_products if _normalize_text(p.get("name", "")).startswith(_normalize_text(base_name))]
            variants = sorted(variants, key=lambda p: p.get("name", ""))
            if len(variants) > 1:
                options = "\\n".join([f"{i+1}. {v.get('name')}" for i, v in enumerate(variants)])
                return f"¿Qué presentación de {base_name} desea?\\n{options}"

        # Missing quantity?
        if qty == 1 and not explicit_qty:
            return f"¿Cuántas unidades desea de {product.get('name')}?"

        # Stock check
        stock = product.get("stock", 0)
        if qty > stock:
            return f"Lo siento, solo hay {stock} unidades de {product.get('name')} disponibles. ¿Desea esa cantidad?"

    # Check delivery date (shared across all items)
    any_delivery = any(itm["delivery"] for itm in order_items)
    if not any_delivery:
        if len(order_items) == 1:
            return f"¿Para qué fecha desea la entrega de {order_items[0]['qty']} unidades de {order_items[0]['product'].get('name')}?"
        return "¿Para qué fecha desea la entrega?"

    # ── All complete: Save to Database! ──
    # If there's an existing order, update it. If not, create it.
    store_id = None
    if not body.order_id:
        store_res = db.table("stores").select("id").eq("user_id", user_id).limit(1).execute().data
        if not store_res:
            return "No tienes tiendas registradas. Por favor crea una sucursal en tu perfil para tomarte el pedido."
        store_id = store_res[0]["id"]
    
    order_id = body.order_id
    total_new = sum(itm["qty"] * itm["product"].get("price", 0) for itm in order_items)
    main_delivery = order_items[0]["delivery"] or global_delivery

    if not order_id:
        # CREATE NEW DRAFT ORDER
        res = db.table("orders").insert({
            "user_id": user_id,
            "store_id": store_id,
            "status": "borrador",
            "delivery_date": main_delivery,
            "notes": zone_notes or "",
            "total": total_new
        }).execute()
        if not res.data:
            return "Hubo un problema guardando tu pedido. Inténtalo de nuevo."
        order_id = res.data[0]["id"]
    else:
        # APPEND TO EXISTING ORDER
        existing_order = db.table("orders").select("total, notes").eq("id", order_id).execute().data
        if existing_order:
            curr_total = float(existing_order[0].get("total", 0))
            curr_notes = existing_order[0].get("notes", "")
            new_notes = f"{curr_notes} | {zone_notes}" if zone_notes else curr_notes
            db.table("orders").update({
                "total": curr_total + total_new,
                "notes": new_notes.strip(" | ")
            }).eq("id", order_id).execute()

    # Create Order Items
    items_to_insert = []
    for itm in order_items:
        items_to_insert.append({
            "order_id": order_id,
            "product_id": itm["product"]["id"],
            "quantity": itm["qty"],
            "unit_price": itm["product"].get("price", 0),
            "subtotal": itm["qty"] * itm["product"].get("price", 0)
        })
    db.table("order_items").insert(items_to_insert).execute()

    # Build confirmation message
    if len(order_items) == 1:
        itm = order_items[0]
        return f"¡Anotado! Agregué {itm['qty']} {itm['product'].get('name')} para {itm['delivery']}. (Puedes decir 'confirma el pedido' cuando termines)"

    lines = ["¡Anotado! Agregué los siguientes productos al pedido:"]
    for itm in order_items:
        delivery = itm["delivery"] or global_delivery or "sin fecha"
        lines.append(f"- {itm['qty']} x {itm['product'].get('name')} (para {delivery})")
    lines.append("\\n(Dime 'confirma el pedido' para procesarlo o pide más productos)")
    
    return "\\n".join(lines)

"""

new_content = content[:start_idx] + new_func + content[end_idx:]

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Updated chat.py successfully!")
