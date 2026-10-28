from pydantic import BaseModel, EmailStr, ConfigDict

class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    full_name: str
    role: str
    entity_ref_id: int | None = None
    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user: UserResponse
