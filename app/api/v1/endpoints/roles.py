from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.api import deps
from app.schemas.role import Role, RoleCreate, RoleUpdate
from app.schemas.common import ResponseBase
from app.crud.role import role_crud
from app.models.user import User

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
    current_user: User = Depends(deps.PermissionChecker(["SUPERADMINISTRATOR"]))
):
    role = await role_crud.create(db, obj_in=role_in)
    return {
        "success": True,
        "message": "Role successfully created",
        "data": role
    }

@router.patch("/{id}", response_model=ResponseBase[Role], summary="Edit Role")
async def update_role(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: str,
    role_in: RoleUpdate,
    current_user: User = Depends(deps.PermissionChecker(["SUPERADMINISTRATOR"]))
):
    role = await role_crud.get(db, id=id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    updated_role = await role_crud.update(db, db_obj=role, obj_in=role_in)
    return {
        "success": True,
        "message": "Role successfully updated",
        "data": updated_role
    }

@router.delete("/{id}", response_model=ResponseBase[Role], summary="Delete Role")
async def delete_role(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: str,
    current_user: User = Depends(deps.PermissionChecker(["SUPERADMINISTRATOR"]))
):
    role = await role_crud.get(db, id=id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    deleted_role = await role_crud.remove(db, id=id)
    return {
        "success": True,
        "message": "Role successfully deleted",
        "data": deleted_role
    }

