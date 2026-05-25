"""Authentication routes: register & login."""

from fastapi import APIRouter, HTTPException, status

from app.config import get_supabase_admin
from app.models.schemas import RegisterRequest, LoginRequest, TokenResponse, UserOut
from app.utils.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    db = get_supabase_admin()

    # Check if email already exists
    existing = db.table("users").select("id").eq("email", body.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    hashed = hash_password(body.password)
    result = db.table("users").insert({
        "name": body.name,
        "email": body.email,
        "phone": body.phone,
        "password_hash": hashed,
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Error al registrar usuario")

    user = result.data[0]
    token = create_access_token({"sub": user["id"], "email": user["email"]})

    return TokenResponse(
        access_token=token,
        user=UserOut(
            id=user["id"],
            name=user["name"],
            email=user["email"],
            phone=user["phone"],
            created_at=user.get("created_at"),
        ),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    db = get_supabase_admin()

    result = db.table("users").select("*").eq("email", body.email).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    user = result.data[0]
    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    token = create_access_token({"sub": user["id"], "email": user["email"]})

    return TokenResponse(
        access_token=token,
        user=UserOut(
            id=user["id"],
            name=user["name"],
            email=user["email"],
            phone=user["phone"],
            created_at=user.get("created_at"),
        ),
    )
