"""Pydantic schemas used across the application."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, List, Literal, Optional
from pydantic import BaseModel, EmailStr, Field


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
    nlp_data: Optional[dict] = None


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
    context: Optional[dict[str, Any]] = None


class ChatMessageOut(BaseModel):
    id: str
    user_id: str
    order_id: Optional[str] = None
    message: str
    sender: str
    created_at: Optional[str] = None
    feedback_rating: Optional[str] = None


class ChatFeedbackRequest(BaseModel):
    rating: Literal["like", "dislike"]
    comment: Optional[str] = None
    context: Optional[dict[str, Any]] = None


class ChatFeedbackOut(BaseModel):
    id: str
    user_id: str
    message_id: str
    order_id: Optional[str] = None
    rating: str
    comment: Optional[str] = None
    context: Optional[dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ──────────────────────────── Notifications ────────────────────────────

class NotificationOut(BaseModel):
    id: str
    user_id: str
    order_id: Optional[str] = None
    type: str
    message: str
    status: str
    created_at: Optional[str] = None


# ──────────────────────────── NLP ────────────────────────────

class NLPParseRequest(BaseModel):
    text: str
    store_id: Optional[str] = None


class NLPProductMatch(BaseModel):
    name: str
    product_id: Optional[str] = None
    quantity: int
    unit_price: float
    subtotal: float


class NLPParseResponse(BaseModel):
    products: List[NLPProductMatch]
    delivery_date: Optional[str] = None
    total: float
    requires_confirmation: bool = True
    message: Optional[str] = None


class NLPParseOrderRequest(BaseModel):
    text: str
    customer_id: Optional[str] = None
    store_id: Optional[str] = None
    user_id: Optional[str] = None
    context: Optional[dict[str, Any]] = None


class NLPSkuCandidate(BaseModel):
    sku_id: Optional[str] = None
    product_id: Optional[str] = None
    product: Optional[str] = None
    presentation: Optional[str] = None
    score: float
    stock: Optional[int] = None
    price: Optional[float] = None


class NLPParsedOrderItem(BaseModel):
    raw_text: str
    producto_detectado: Optional[str] = None
    producto_normalizado: Optional[str] = None
    presentacion: Optional[str] = None
    unidad: Optional[str] = None
    cantidad: int
    cantidad_detectada: bool = True
    sku_id: Optional[str] = None
    product_id: Optional[str] = None
    confidence: float
    sku_candidates: List[NLPSkuCandidate] = Field(default_factory=list)
    requires_clarification: bool = False
    clarification_reason: Optional[str] = None


class NLPClarificationQuestion(BaseModel):
    type: str
    message: str
    item_index: Optional[int] = None
    options: Optional[list[dict[str, Any]]] = None


class NLPParseOrderResponse(BaseModel):
    intent: str
    store_id: Optional[str] = None
    customer_id: Optional[str] = None
    fecha_entrega: Optional[str] = None
    items: List[NLPParsedOrderItem]
    requires_clarification: bool
    clarification_questions: List[NLPClarificationQuestion] = Field(default_factory=list)
    validation_status: str
    confidence_score: float
    interaction_id: Optional[str] = None
    message: Optional[str] = None


class NLPDraftOrderResponse(NLPParseOrderResponse):
    draft_created: bool = False
    order: Optional[OrderOut] = None


class NLPValidateExtractionRequest(BaseModel):
    store_id: Optional[str] = None
    delivery_date: Optional[date] = None
    items: List[OrderItemCreate]


class NLPValidationIssue(BaseModel):
    type: str
    message: str
    product_id: Optional[str] = None


class NLPValidationResponse(BaseModel):
    validation_status: str
    requires_clarification: bool
    issues: List[NLPValidationIssue] = Field(default_factory=list)


class NLPCorrectionRequest(BaseModel):
    interaction_id: str
    original_extraction: dict[str, Any]
    corrected_extraction: dict[str, Any]
    correction_reason: Optional[str] = None
