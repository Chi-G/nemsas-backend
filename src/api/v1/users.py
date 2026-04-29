from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import deps
from src.db.base import get_db
from src.schemas.user import User, UserCreate, UserUpdate
from src.schemas.response import BaseResponse, PaginatedData
import math
from src.services.user import user_service
from src.db.models.user import User as DBUser
from src.core.rbac import Permission as PermissionEnum

router = APIRouter()

@router.get("/", response_model=BaseResponse[PaginatedData[User]])
async def read_users(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    role_id: Optional[int] = None,
    provider_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    current_user: DBUser = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.USER_READ])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Retrieve users. (Admins only)
    Supports filtering by role, provider, and status. Automatically scoped to state for SEMSAS Admins.
    """
    items = await user_service.list(
        db, 
        role_id=role_id, 
        state_id=state_id, 
        provider_id=provider_id, 
        is_active=is_active, 
        skip=skip, 
        limit=limit
    )
    total = await user_service.count(
        db, 
        role_id=role_id, 
        state_id=state_id, 
        provider_id=provider_id, 
        is_active=is_active
    )
    
    total_pages = math.ceil(total / limit) if limit > 0 else 1
    page = (skip // limit) + 1 if limit > 0 else 1

    return BaseResponse(
        success=True,
        message="Users successfully fetched",
        data=PaginatedData(
            items=items,
            totalCount=total,
            page=page,
            pageSize=limit,
            totalPages=total_pages
        ),
        totalCount=total
    )

@router.post("/", response_model=BaseResponse[User])
async def create_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate,
    current_user: DBUser = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.USER_MANAGE])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Create a new user. (Admins only)
    Automatically triggers an activation email with a secure link.
    """
    # SEMSAS Admin isolation
    if state_id and user_in.state_id != state_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SEMSAS Admins can only create users in their assigned state"
        )
        
    # Password should be generated or handled via activation link
    user = await user_service.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(status_code=400, detail="User already exists")
    created_user = await user_service.create(db, obj_in=user_in, password="temporary_password_to_be_reset")
    return BaseResponse(
        success=True,
        message="User created successfully",
        data=created_user
    )

@router.patch("/{id}", response_model=BaseResponse[User])
async def update_user(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    user_in: UserUpdate,
    current_user: DBUser = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.USER_MANAGE])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Update a user. (Admins only)
    """
    user = await user_service.get_by_id(db, user_id=id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # SEMSAS Admin isolation
    if state_id and user.state_id != state_id:
        raise HTTPException(status_code=403, detail="Access denied: User belongs to another state")
        
    updated_user = await user_service.update(db, db_obj=user, obj_in=user_in)
    return BaseResponse(
        success=True,
        message="User updated successfully",
        data=updated_user
    )

@router.delete("/{id}", response_model=BaseResponse[User])
async def deactivate_user(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    current_user: DBUser = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.USER_MANAGE])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Deactivate a user. (Admins only)
    """
    user = await user_service.get_by_id(db, user_id=id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # SEMSAS Admin isolation
    if state_id and user.state_id != state_id:
        raise HTTPException(status_code=403, detail="Access denied: User belongs to another state")
        
    deactivated_user = await user_service.deactivate(db, db_obj=user)
    return BaseResponse(
        success=True,
        message="User deactivated successfully",
        data=deactivated_user
    )
