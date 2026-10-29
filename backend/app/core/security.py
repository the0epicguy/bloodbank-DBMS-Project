"""
Security utilities (Person 4): password hashing, JWT tokens, and the
FastAPI dependencies used to protect endpoints.

How login works
---------------
    1. Client POSTs username + password to /auth/login
    2. We check the password against the bcrypt hash in `user_account`
    3. We return a signed JWT:  { sub: user_id, role: ..., exp: ... }
    4. Client sends it back on every request:  Authorization: Bearer <token>
    5. `get_current_user` verifies the signature + expiry and loads the user

Using it on an endpoint
-----------------------
    @router.get("/something")
    def something(user = Depends(get_current_user)): ...                 # any logged-in user

    @router.post("/something")
    def something(user = Depends(require_roles("ADMIN", "BANK_STAFF"))): ...   # only these roles
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

# auto_error=False so WE return a clean 401 JSON instead of FastAPI's default
bearer_scheme = HTTPBearer(auto_error=False)

ROLES = ("ADMIN", "BANK_STAFF", "HOSPITAL_STAFF", "DONOR")


# ---------------------------------------------------------------- passwords
def hash_password(password: str) -> str:
    """bcrypt-hash a password (bcrypt only looks at the first 72 bytes)."""
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """True if `password` matches the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8")[:72], password_hash.encode("utf-8"))
    except ValueError:
        return False


# --------------------------------------------------------------------- JWT
def create_access_token(
    user_id: int, role: str, expires_minutes: Optional[int] = None
) -> str:
    """Create a signed JWT for a user."""
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
    """Verify signature + expiry and return the payload. Raises Unauthorized."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise Unauthorized("Session expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise Unauthorized("Invalid authentication token")


# ------------------------------------------------------------ dependencies
def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> UserAccount:
    """
    FastAPI dependency: returns the logged-in UserAccount or raises 401.
    (Integration contract: `get_current_user` -> User, used by everyone.)
    """
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
    """
    Dependency factory: only let users with one of `allowed_roles` through.
    Returns the user so the endpoint can use it.
    """

    def checker(user: UserAccount = Depends(get_current_user)) -> UserAccount:
        if user.role not in allowed_roles:
            raise Forbidden(
                f"Role '{user.role}' is not allowed here. "
                f"Required: {', '.join(allowed_roles)}"
            )
        return user

    return checker
