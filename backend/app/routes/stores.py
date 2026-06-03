"""Store CRUD routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from ..config import get_supabase_admin
from ..models.schemas import StoreCreate, StoreUpdate, StoreOut
from ..utils.auth import get_current_user_id

router = APIRouter(prefix="/stores", tags=["stores"])


@router.post("/", response_model=StoreOut, status_code=status.HTTP_201_CREATED)
async def create_store(body: StoreCreate, user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    result = db.table("stores").insert({
        "user_id": user_id,
        "name": body.name,
        "address": body.address,
        "latitude": body.latitude,
        "longitude": body.longitude,
        "phone": body.phone,
        "notes": body.notes,
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Error al crear tienda")
    return StoreOut(**result.data[0])


@router.get("/", response_model=list[StoreOut])
async def list_stores(user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    result = db.table("stores").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return [StoreOut(**s) for s in result.data]


@router.get("/{store_id}", response_model=StoreOut)
async def get_store(store_id: str, user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    result = db.table("stores").select("*").eq("id", store_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")
    return StoreOut(**result.data[0])


@router.put("/{store_id}", response_model=StoreOut)
async def update_store(store_id: str, body: StoreUpdate, user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")

    result = db.table("stores").update(updates).eq("id", store_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")
    return StoreOut(**result.data[0])


@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_store(store_id: str, user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    result = db.table("stores").delete().eq("id", store_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")
