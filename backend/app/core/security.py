from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import bcrypt
from app.core.config import settings

ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def verify_password(password: str, password_hash: str) -> bool:
    try:
        pwd_bytes = password.encode("utf-8")[:72]
        hash_bytes = password_hash.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False

def create_access_token(subject: str, role: str, expires_minutes: int | None = None) -> str:
    expiry = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes or settings.jwt_expire_minutes)
    return jwt.encode({"sub": subject, "role": role, "exp": expiry}, settings.jwt_secret, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid or expired access token") from exc
