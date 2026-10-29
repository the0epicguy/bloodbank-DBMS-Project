"""
Auth Router (Person 4).

Endpoints:
    POST /auth/login               - username + password -> JWT
    POST /auth/demo-login/{role}   - 1-click login (ADMIN, BANK_STAFF, HOSPITAL_STAFF, DONOR)
    GET  /auth/me                  - who am I? (needs a token)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import UserAccount
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Log in with username + password and receive a JWT."""
    return auth_service.login(db, data.username, data.password)


@router.post("/demo-login/{role}", response_model=TokenResponse)
def demo_login(role: str, db: Session = Depends(get_db)):
    """1-click demo login for a role (disabled when ALLOW_DEMO_LOGIN=false)."""
    return auth_service.demo_login(db, role)


@router.get("/me", response_model=UserResponse)
def me(user: UserAccount = Depends(get_current_user)):
    """Return the currently logged-in user."""
    return user
