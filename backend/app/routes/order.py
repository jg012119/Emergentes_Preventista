from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import re

router = APIRouter()

# Catalog of available liquid products (official name -> set of synonyms)
CATALOG = {
    "Coca-Cola Normal": {"coca", "coquita", "gaseosa negra", "refresco"},
    "Agua Cielo / Vital": {"agua", "agüita", "agua sin gas", "h2o", "hidratación"},
    # Add more products here as needed
}

# Words that indicate solid food requests
SOLID_KEYWORDS = {"papas", "papitas", "papas fritas", "nachos", "galletas", "dulce", "hamburguesa", "pizza", "sandwich", "bocadillo", "comida", "alimento", "snack", "papas chips"}

# Words that indicate alcohol requests
ALCOHOL_KEYWORDS = {"cheba", "cerveza", "birra", "chela", "vino", "whisky", "ron", "vodka", "licor"}

class OrderRequest(BaseModel):
    message: str

def normalize(text: str) -> str:
    return text.lower()

def find_product(token: str):
    for official, synonyms in CATALOG.items():
        if token in synonyms:
            return official
    return None

@router.post("/process-order", tags=["order"])
def process_order(req: OrderRequest):
    msg = normalize(req.message)
    # Split by commas or "y" to handle multiple items
    items = re.split(r"[ ,]+y[ ,]+|[ ,]+", msg)
    items = [i.strip() for i in items if i.strip()]
    responses = []
    for item in items:
        # Check for solid food
        if any(word in item for word in SOLID_KEYWORDS):
            responses.append(f"❌ *{item}* – Lamento informarte que no contamos con eso, ya que nos especializamos exclusivamente en el abastecimiento de productos líquidos y bebidas.")
            continue
        # Check for alcohol
        if any(word in item for word in ALCOHOL_KEYWORDS):
            responses.append(f"❌ *{item}* – Lamento informarte que no distribuimos bebidas alcohólicas.")
            continue
        # Check catalog synonyms
        matched = None
        for official, synonyms in CATALOG.items():
            if item in synonyms:
                matched = official
                break
        if matched:
            responses.append(f"✅ *{item}* – Disponible como **{matched}**.")
        else:
            # Not found, suggest closest (first product)
            first_product = list(CATALOG.keys())[0]
            responses.append(f"❌ *{item}* – No lo tenemos en nuestro inventario. ¿Te gustaría cambiarlo por **{first_product}**?")
    # Build final reply
    reply = "¡Hola! 😊 Con gusto procesaré tu pedido.\n\n" + "\n".join(responses) + "\n\n¿Confirmas los productos indicados?"
    return {"reply": reply}
