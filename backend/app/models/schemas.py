"""Pydantic schemas used across the application."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr


# ──────────────────────────── Auth ────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


# ──────────────────────────── Users ────────────────────────────

class UserOut(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    created_at: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None


# ──────────────────────────── Stores ────────────────────────────

class StoreCreate(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    phone: Optional[str] = None
    notes: Optional[str] = None


class StoreUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    notes: Optional[str] = None


class StoreOut(BaseModel):
    id: str
    user_id: str
    name: str
    address: str
    latitude: float
    longitude: float
    phone: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None


# ──────────────────────────── Products ────────────────────────────

class ProductCreate(BaseModel):
    name: str
    category: str
    price: float
    stock: int
    active: bool = True


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    active: Optional[bool] = None


class ProductOut(BaseModel):
    id: str
    name: str
    category: str
    price: float
    stock: int
    active: bool
    created_at: Optional[str] = None


# ──────────────────────────── Orders ────────────────────────────

class OrderItemCreate(BaseModel):
    product_id: str
    quantity: int


class OrderDraftRequest(BaseModel):
    store_id: str
    delivery_date: date
    notes: Optional[str] = None
    items: List[OrderItemCreate]


class OrderItemOut(BaseModel):
    id: str
    order_id: str
    product_id: str
    product_name: Optional[str] = None
    quantity: int
    unit_price: float
    subtotal: float


class OrderOut(BaseModel):
    id: str
    user_id: str
    store_id: str
    store_name: Optional[str] = None
    status: str
    delivery_date: Optional[str] = None
    total: float
    notes: Optional[str] = None
    created_at: Optional[str] = None
    items: Optional[List[OrderItemOut]] = None
    nlp_data: Optional[dict] = None


class OrderStatusUpdate(BaseModel):
    status: str  # pendiente, confirmado, rechazado, en_proceso


class OrderDeliveryDateUpdate(BaseModel):
    delivery_date: date


# ──────────────────────────── Chat ────────────────────────────

class ChatMessageCreate(BaseModel):
    order_id: Optional[str] = None
    message: str
    sender: str = "user"  # user | system | empresa


class ChatMessageOut(BaseModel):
    id: str
    user_id: str
    order_id: Optional[str] = None
    message: str
    sender: str
    created_at: Optional[str] = None


# ──────────────────────────── Notifications ────────────────────────────

class NotificationOut(BaseModel):
    id: str
    user_id: str
    order_id: Optional[str] = None
    type: str
    message: str
    status: str
    created_at: Optional[str] = None


# ──────────────────────────── NLP (placeholder for Sprint 2) ────────

class NLPParseRequest(BaseModel):
    text: str
    store_id: Optional[str] = None

class NLPParseResponse(BaseModel):
    order: dict  # OrderDraftRequest compatible dict
    nlp_data: dict
    questions: list[dict] | None = None
