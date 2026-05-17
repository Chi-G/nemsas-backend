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
    state_id: Optional[int] = None,
    current_user: User = Depends(deps.PermissionChecker(["SUPERADMINISTRATOR", "ADMINSEMSASUSER"])),
):
    """
    Get all users (SUPERADMINISTRATOR can see all or filter by state, ADMINSEMSASUSER only their state)
    """
    actual_skip = offset if offset is not None else skip
    
    # Logic for state filtering:
    # 1. ADMINSEMSASUSER is strictly limited to their own state.
    # 2. SUPERADMINISTRATOR can filter by state_id query param if provided, otherwise sees all.
    effective_state_id = None
    
    if current_user.user_type == "ADMINSEMSASUSER":
        effective_state_id = current_user.state_id
    elif current_user.user_type == "SUPERADMINISTRATOR":
        effective_state_id = state_id
        
    users, total = await user_crud.get_multi_with_count(
        db, 
        skip=actual_skip, 
        limit=limit, 
        search=search,
        state_id=effective_state_id
    )
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
    current_user: User = Depends(deps.PermissionChecker(["SUPERADMINISTRATOR", "ADMINSEMSASUSER"])),
):
    # Role-based validation for creation
    if current_user.user_type == "ADMINSEMSASUSER":
        # 1. Enforce state restriction
        if user_in.state_id != current_user.state_id:
            raise HTTPException(
                status_code=403,
                detail={
                    "message": "User creation failed",
                    "error": f"You can only create users for your own state (ID: {current_user.state_id})"
                }
            )
        
        # 2. Enforce allowed roles
        allowed_roles = [
            "SEMSASUSER", 
            "SEMSASDISPATCH", 
            "AMBULANCEUSER", 
            "EMERGENCYTREATMENTUSER", 
            "STATEVIEWER"
        ]
        if user_in.user_type not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail={
                    "message": "User creation failed",
                    "error": f"You are not authorized to create users with the role '{user_in.user_type}'. Allowed roles: {', '.join(allowed_roles)}"
                }
            )

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

@router.get("/me/notifications", response_model=ResponseBase[List[dict]])
async def get_my_notifications(
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get all cached/pending notifications from Redis
    """
    from app.core.notifications import notification_service
    notifications = await notification_service.get_pending_notifications(str(current_user.id))
    return {
        "success": True,
        "message": "Notifications fetched",
        "data": notifications
    }

@router.post("/me/notifications/{notif_id}/read", response_model=ResponseBase[bool])
async def mark_notification_as_read(
    notif_id: str,
    current_user: User = Depends(deps.get_current_user),
):
    """
    Mark a notification as read in Redis
    """
    from app.core.notifications import notification_service
    await notification_service.mark_as_read(str(current_user.id), notif_id)
    return {
        "success": True,
        "message": "Notification marked as read",
        "data": True
    }
