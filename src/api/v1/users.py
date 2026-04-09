from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import deps
from src.db.base import get_db
from src.schemas.user import User, UserCreate, UserUpdate
from src.services.user import user_service
from src.db.models.user import User as DBUser
from src.core.rbac import Permission as PermissionEnum

router = APIRouter()

@router.get("/", response_model=List[User])
async def read_users(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    role_id: Optional[int] = None,
    current_user: DBUser = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.USER_READ])),
    state_id: Optional[int] = Depends(deps.get_state_scope),
) -> Any:
    """
    Retrieve users. (Admins only)
    """
    return await user_service.list(db, role_id=role_id, state_id=state_id, skip=skip, limit=limit)

@router.post("/", response_model=User)
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
    """
    # SEMSAS Admin can only create users in their own state
    if state_id and user_in.state_id != state_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SEMSAS Admins can only create users in their assigned state"
        )
        
    # Password should be generated or handled via activation link
    user = await user_service.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(status_code=400, detail="User already exists")
    return await user_service.create(db, obj_in=user_in, password="temporary_password_to_be_reset")

@router.patch("/{id}", response_model=User)
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
        
    return await user_service.update(db, db_obj=user, obj_in=user_in)

@router.delete("/{id}", response_model=User)
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
        
    return await user_service.deactivate(db, db_obj=user)
