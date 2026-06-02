"""Notification service – chat + email notifications on status changes."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD

STATUS_LABELS = {
    "pendiente": "Pendiente",
    "confirmado": "Confirmado",
    "rechazado": "Rechazado",
    "en_proceso": "En Proceso",
    "pagado": "Pagado",
}


async def notify_status_change(db, order: dict, new_status: str):
    """Create chat notification and send email when order status changes."""
    user_id = order["user_id"]
    order_id = order["id"]
    label = STATUS_LABELS.get(new_status, new_status)

    # Build summary
    items = db.table("order_items").select("*, products(name)").eq("order_id", order_id).execute()
    lines = []
    for item in items.data:
        pname = item.get("products", {}).get("name", "Producto") if isinstance(item.get("products"), dict) else "Producto"
        lines.append(f"- {pname} x{item['quantity']}")
    summary = "\n".join(lines)

    chat_msg = (
        f"Tu pedido #{order_id[:8]} fue {label.lower()} por AJE.\n\n"
        f"Resumen:\n{summary}\n"
        f"Total: Bs {order['total']:.2f}\n"
        f"Estado: {label}"
    )

    # Save chat message
    db.table("chat_messages").insert({
        "user_id": user_id,
        "order_id": order_id,
        "message": chat_msg,
        "sender": "system",
    }).execute()

    # Save notification record
    db.table("notifications").insert({
        "user_id": user_id,
        "order_id": order_id,
        "type": "chat",
        "message": chat_msg,
        "status": "enviado",
    }).execute()

    # Try sending email
    user = db.table("users").select("email, name").eq("id", user_id).execute()
    if user.data and EMAIL_USER:
        try:
            await _send_email(
                to_email=user.data[0]["email"],
                to_name=user.data[0]["name"],
                subject=f"Pedido #{order_id[:8]} — {label}",
                body=chat_msg,
                order_id=order_id,
                user_id=user_id,
                db=db,
            )
        except Exception:
            # Log but don't fail the request
            db.table("notifications").insert({
                "user_id": user_id,
                "order_id": order_id,
                "type": "email",
                "message": f"Error al enviar correo sobre pedido #{order_id[:8]}",
                "status": "fallido",
            }).execute()


async def _send_email(to_email: str, to_name: str, subject: str, body: str, order_id: str, user_id: str, db):
    """Send email via SMTP."""
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = subject

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #1a73e8;">Preventista Inteligente — AJE</h2>
        <p>Hola <strong>{to_name}</strong>,</p>
        <pre style="background: #f5f5f5; padding: 16px; border-radius: 8px;">{body}</pre>
        <p style="color: #666; font-size: 12px;">Este es un mensaje automático del sistema de pedidos.</p>
    </body>
    </html>
    """
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)

    # Record success
    db.table("notifications").insert({
        "user_id": user_id,
        "order_id": order_id,
        "type": "email",
        "message": f"Correo enviado a {to_email}: {subject}",
        "status": "enviado",
    }).execute()
