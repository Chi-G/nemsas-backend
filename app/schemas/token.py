from typing import Optional
from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    status: str = "success"
    message: str = "Login successful"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    state_id: Optional[int] = None

class LoginRequest(BaseModel):
    email: str # Using str to match your flexible email handling
    password: str
