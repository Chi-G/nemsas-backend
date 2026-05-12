from pydantic import BaseModel

class RoleBase(BaseModel):
    id: str
    name: str

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    name: str

class Role(RoleBase):
    class Config:
        from_attributes = True
