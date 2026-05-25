"""Chat message routes."""

from fastapi import APIRouter, Depends, HTTPException

from app.config import get_supabase_admin
from app.models.schemas import ChatMessageCreate, ChatMessageOut
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatMessageOut, status_code=201)
async def send_message(body: ChatMessageCreate, user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    result = db.table("chat_messages").insert({
        "user_id": user_id,
        "order_id": body.order_id,
        "message": body.message,
        "sender": body.sender,
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Error al enviar mensaje")
    return ChatMessageOut(**result.data[0])


@router.get("/general/messages", response_model=list[ChatMessageOut])
async def get_general_chat(user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    result = (
        db.table("chat_messages")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at")
        .execute()
    )
    general_messages = [m for m in result.data if m.get("order_id") is None]
    return [ChatMessageOut(**m) for m in general_messages[-100:]]


@router.get("/{order_id}", response_model=list[ChatMessageOut])
async def get_chat(order_id: str, _user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    result = (
        db.table("chat_messages")
        .select("*")
        .eq("order_id", order_id)
        .order("created_at")
        .execute()
    )
    return [ChatMessageOut(**m) for m in result.data]


@router.get("/user/all", response_model=list[ChatMessageOut])
async def get_user_chats(user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    result = (
        db.table("chat_messages")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(100)
        .execute()
    )
    return [ChatMessageOut(**m) for m in result.data]
