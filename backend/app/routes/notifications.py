"""Notification routes."""

from fastapi import APIRouter, Depends

from app.config import get_supabase_admin
from app.models.schemas import NotificationOut
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=list[NotificationOut])
async def list_notifications(user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    result = (
        db.table("notifications")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return [NotificationOut(**n) for n in result.data]
