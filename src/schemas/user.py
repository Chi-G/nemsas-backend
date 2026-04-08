from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime

class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None

class Permission(PermissionBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class Role(RoleBase):
    id: int
    permissions: List[Permission] = []
    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    email: EmailStr
    name: str
    is_active: bool = True
    provider_id: Optional[int] = None
    state_id: Optional[int] = None
    lga_id: Optional[int] = None

class UserCreate(UserBase):
    role_id: int # Password is not accepted in creation, handled via activation email

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role_id: Optional[int] = None
    provider_id: Optional[int] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: int
    role: Role
    last_login: Optional[datetime] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    type: Optional[str] = None
