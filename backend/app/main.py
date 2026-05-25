"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, users, stores, products, orders, chat, notifications

app = FastAPI(
    title="Preventista Inteligente AJE",
    description="MVP de agente inteligente para recepción y gestión de pedidos mediante lenguaje natural.",
    version="1.0.0",
)

# CORS – allow mobile app and panel to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(stores.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(chat.router)
app.include_router(notifications.router)


@app.get("/", tags=["health"])
async def health():
    return {"status": "ok", "service": "Preventista Inteligente AJE"}
