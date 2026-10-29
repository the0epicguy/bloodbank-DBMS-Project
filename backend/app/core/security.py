"""
Security utilities: bcrypt password hashing + JWT token creation/verification,
plus FastAPI dependencies for auth-guarding endpoints.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.errors import Forbidden, Unauthorized
from app.models.user import UserAccount

bearer_scheme = HTTPBearer(auto_error=False)

# Valid role names used across the application.
ROLES = {"ADMIN", "BANK_STAFF", "HOSPITAL_STAFF", "DONOR"}


# ── Password hashing ──────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8")[:72], password_hash.encode("utf-8"))
    except ValueError:
        return False


# ── JWT ───────────────────────────────────────────────────────────────────

def create_access_token(user_id: int, role: str, expires_minutes: Optional[int] = None) -> str:
    now = datetime.now(timezone.utc)
    minutes = settings.JWT_EXPIRE_MINUTES if expires_minutes is None else expires_minutes
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise Unauthorized("Session expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise Unauthorized("Invalid authentication token")


# ── FastAPI dependencies ──────────────────────────────────────────────────

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> UserAccount:
    if credentials is None or not credentials.credentials:
        raise Unauthorized("Not authenticated")
    payload = decode_token(credentials.credentials)
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise Unauthorized("Invalid authentication token")
    user = db.query(UserAccount).filter(UserAccount.user_id == user_id).first()
    if user is None:
        raise Unauthorized("User no longer exists")
    return user


def require_roles(*allowed_roles: str):
    def checker(user: UserAccount = Depends(get_current_user)) -> UserAccount:
        if user.role not in allowed_roles:
            raise Forbidden(
                f"Role '{user.role}' not permitted. Required: {', '.join(allowed_roles)}"
            )
        return user
    return checker
