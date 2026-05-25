"""User profile routes."""

from fastapi import APIRouter, Depends, HTTPException

from app.config import get_supabase_admin
from app.models.schemas import UserOut, UserUpdate
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    result = db.table("users").select("*").eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    u = result.data[0]
    return UserOut(
        id=u["id"], name=u["name"], email=u["email"],
        phone=u["phone"], created_at=u.get("created_at"),
    )


@router.put("/me", response_model=UserOut)
async def update_me(body: UserUpdate, user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")

    result = db.table("users").update(updates).eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    u = result.data[0]
    return UserOut(
        id=u["id"], name=u["name"], email=u["email"],
        phone=u["phone"], created_at=u.get("created_at"),
    )
