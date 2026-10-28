from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, hash_password
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])
DEMO = {
    "ADMIN": ("demo_admin", "admin@example.test", "Demo Administrator", None),
    "BANK_STAFF": ("demo_bank", "bank@example.test", "Demo Bank Staff", 1),
    "HOSPITAL_STAFF": ("demo_hospital", "hospital@example.test", "Demo Hospital Staff", 1),
    "DONOR": ("demo_donor", "donor@example.test", "Demo Donor", 1),
}

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.username == payload.username))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    token = create_access_token(user.username, user.role)
    return {"access_token": token, "token_type": "bearer", "role": user.role, "user": user}

@router.post("/demo-login/{role}", response_model=TokenResponse)
async def demo_login(role: str, db: AsyncSession = Depends(get_db)):
    role = role.upper()
    if role not in DEMO:
        raise HTTPException(404, "Unknown demo role")
    if not settings.seed_demo_users:
        raise HTTPException(403, "Demo login is disabled. Set SEED_DEMO_USERS=true for local demos.")
    username, email, full_name, entity_ref_id = DEMO[role]
    user = await db.scalar(select(User).where(User.username == username))
    if user is None:
        user = User(username=username, email=email, full_name=full_name, role=role,
                    entity_ref_id=entity_ref_id, password_hash=hash_password("DemoOnly!123"))
        db.add(user)
        await db.commit()
        await db.refresh(user)
    token = create_access_token(user.username, user.role)
    return {"access_token": token, "token_type": "bearer", "role": user.role, "user": user}

@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user
