from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.api import deps
from app.schemas.role import Role, RoleCreate
from app.schemas.common import ResponseBase
from app.crud.role import role_crud

router = APIRouter()

@router.get("/", response_model=ResponseBase[List[Role]])
async def read_roles(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100
):
    roles = await role_crud.get_multi(db, skip=skip, limit=limit)
    return {
        "success": True,
        "message": "Role(s) successfully fetched",
        "data": roles
    }

@router.post("/", response_model=ResponseBase[Role])
async def create_role(
    *,
    db: AsyncSession = Depends(deps.get_db),
    role_in: RoleCreate,
):
    role = await role_crud.create(db, obj_in=role_in)
    return {
        "success": True,
        "message": "Role successfully created",
        "data": role
    }
