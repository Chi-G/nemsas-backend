from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.api import deps
from app.schemas.user import User as UserSchema, UserCreate
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationMeta, ResponseBase
from app.crud.user import user_crud
from sqlalchemy.future import select

router = APIRouter()

@router.get("/me", response_model=ResponseBase[UserSchema])
async def read_user_me(
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get current user details
    """
    return {
        "success": True,
        "message": "User details successfully fetched",
        "data": current_user
    }

@router.get("/", response_model=PaginatedResponse[UserSchema])
async def read_users(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    offset: Optional[int] = None,
    search: Optional[str] = None,
    current_user: User = Depends(deps.PermissionChecker(["SUPERADMINISTRATOR"])),
):
    """
    Get all users (SUPERADMINISTRATOR only)
    """
    actual_skip = offset if offset is not None else skip
    users, total = await user_crud.get_multi_with_count(db, skip=actual_skip, limit=limit, search=search)
    return {
        "success": True,
        "message": "User(s) fetched",
        "data": users,
        "meta": {
            "total": total,
            "skip": actual_skip,
            "limit": limit
        }
    }

@router.post("/", response_model=ResponseBase[UserSchema])
async def create_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_in: UserCreate,
    current_user: User = Depends(deps.PermissionChecker(["SUPERADMINISTRATOR"])),
):
    # Check if user exists (email)
    existing_user_email = await user_crud.get_by_email(db, email=user_in.email)
    if existing_user_email:
        print(f"CONFLICT: Email {user_in.email} already exists")
        raise HTTPException(
            status_code=400,
            detail={
                "message": "User registration failed",
                "error": f"A user with email '{user_in.email}' already exists"
            }
        )

    # Check if user exists (username)
    existing_user_name = await user_crud.get_by_username(db, user_name=user_in.user_name)
    if existing_user_name:
        print(f"CONFLICT: Username {user_in.user_name} already exists")
        raise HTTPException(
            status_code=400,
            detail={
                "message": "User registration failed",
                "error": f"A user with username '{user_in.user_name}' already exists"
            }
        )


        
    new_user = await user_crud.create(db, obj_in=user_in)
    return {
        "success": True,
        "message": "User successfully created",
        "data": new_user
    }
