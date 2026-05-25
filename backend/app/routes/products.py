"""Product CRUD routes (admin / AJE operations)."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import get_supabase_admin
from app.models.schemas import ProductCreate, ProductUpdate, ProductOut
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(body: ProductCreate, _user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    result = db.table("products").insert({
        "name": body.name,
        "category": body.category,
        "price": body.price,
        "stock": body.stock,
        "active": body.active,
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Error al crear producto")
    return ProductOut(**result.data[0])


@router.get("/", response_model=list[ProductOut])
async def list_products():
    """Public endpoint – any user can see the catalogue."""
    db = get_supabase_admin()
    result = (
        db.table("products")
        .select("*")
        .eq("active", True)
        .order("category")
        .order("name")
        .execute()
    )
    return [ProductOut(**p) for p in result.data]


@router.get("/all", response_model=list[ProductOut])
async def list_all_products(_user_id: str = Depends(get_current_user_id)):
    """Admin endpoint – includes inactive products."""
    db = get_supabase_admin()
    result = db.table("products").select("*").order("category").order("name").execute()
    return [ProductOut(**p) for p in result.data]


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: str):
    db = get_supabase_admin()
    result = db.table("products").select("*").eq("id", product_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return ProductOut(**result.data[0])


@router.put("/{product_id}", response_model=ProductOut)
async def update_product(product_id: str, body: ProductUpdate, _user_id: str = Depends(get_current_user_id)):
    db = get_supabase_admin()
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")

    result = db.table("products").update(updates).eq("id", product_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return ProductOut(**result.data[0])


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: str, _user_id: str = Depends(get_current_user_id)):
    """Soft-delete: sets active=false."""
    db = get_supabase_admin()
    result = db.table("products").update({"active": False}).eq("id", product_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
