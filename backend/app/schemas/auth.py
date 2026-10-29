"""
Pydantic schemas for authentication (Person 4).
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Body of POST /auth/login."""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class UserResponse(BaseModel):
    """A user as returned to the client (never includes the password hash)."""
    user_id: int
    username: str
    email: str
    full_name: str
    role: str
    entity_ref_id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Response of /auth/login and /auth/demo-login/{role}."""
    access_token: str
    token_type: str = "bearer"
    role: str
    user: UserResponse
