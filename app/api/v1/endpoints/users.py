from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from app.api import deps
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationMeta, ResponseBase
from app.crud.user import user_crud
from sqlalchemy.future import select

router = APIRouter()

@router.get("/me", response_model=ResponseBase[UserSchema])
async def read_user_me(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get current user details
    """
    user_data = UserSchema.model_validate(current_user)
    
    if current_user.user_type == "AMBULANCEUSER" and current_user.ambulance_id:
        from app.models.ambulance import Ambulance
        from sqlalchemy.orm import selectinload
        stmt = select(Ambulance).where(Ambulance.id == current_user.ambulance_id).options(selectinload(Ambulance.ambulance_type))
        result = await db.execute(stmt)
        ambulance = result.scalar_one_or_none()
        if ambulance and ambulance.ambulance_type:
            user_data.ambulance_type = ambulance.ambulance_type.name
            
    elif current_user.user_type == "EMERGENCYTREATMENTUSER" and current_user.emergency_treatment_center_id:
        from app.models.hospital import Hospital
        from sqlalchemy.orm import selectinload
        stmt = select(Hospital).where(Hospital.id == current_user.emergency_treatment_center_id).options(selectinload(Hospital.hospital_type))
        result = await db.execute(stmt)
        hospital = result.scalar_one_or_none()
        if hospital:
            hospital_type_name = hospital.hospital_type.name if hospital.hospital_type else None
            user_data.etc_details = {
                "id": hospital.id, 
                "name": hospital.name,
                "hospital_type": hospital_type_name,
                "address1": hospital.address1,
                "latitude": hospital.latitude,
                "longitude": hospital.longitude,
                "location": hospital.location,
                "address2": hospital.address2,
                "landmark": hospital.landmark,
                "nhia_or_shia": hospital.nhia_or_shia,
                "date_added": hospital.date_added,
                "status": hospital.status,
                "state_id": hospital.state_id,
                "lga_id": hospital.lga_id
            }

    return {
        "success": True,
        "message": "User details successfully fetched",
        "data": user_data
    }

from pydantic import BaseModel

class StatusUpdate(BaseModel):
    status: bool

@router.patch("/me/status", response_model=ResponseBase[UserSchema])
async def update_my_status(
    *,
    db: AsyncSession = Depends(deps.get_db),
    status_in: StatusUpdate,
    current_user: User = Depends(deps.get_current_user),
):
    """
    Update the general status of the current user
    """
    current_user.status = status_in.status
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    
    user_data = UserSchema.model_validate(current_user)
    return {
        "success": True,
        "message": "User status successfully updated",
        "data": user_data
    }

@router.get("/", response_model=PaginatedResponse[UserSchema])
async def read_users(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    offset: Optional[int] = None,
    search: Optional[str] = None,
    state_id: Optional[int] = None,
    current_user: User = Depends(deps.PermissionChecker(["SUPERADMINISTRATOR", "ADMINSEMSASUSER","NATIONALVIEWER", "STATEVIEWER",'PERMSEC'])),
):
    """
    Get all users (SUPERADMINISTRATOR can see all or filter by state, ADMINSEMSASUSER only their state)
    """
    actual_skip = offset if offset is not None else skip
    
    # Logic for state filtering:
    # 1. ADMINSEMSASUSER is strictly limited to their own state.
    # 2. SUPERADMINISTRATOR can filter by state_id query param if provided, otherwise sees all.
    effective_state_id = None
    
    if current_user.user_type in ["ADMINSEMSASUSER", "STATEVIEWER"]:
        effective_state_id = current_user.state_id
    elif current_user.user_type == "SUPERADMINISTRATOR":
        effective_state_id = state_id
    elif current_user.user_type == "PERMSEC":
        effective_state_id = state_id
    elif current_user.user_type == "NATIONALVIEWER":
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

@router.delete("/{id}", response_model=ResponseBase[UserSchema], summary="(Disable User)")
async def delete_user(
    id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.PermissionChecker(["SUPERADMINISTRATOR", "ADMINSEMSASUSER"])),
):
    """
    Disable a user (set is_active to False) instead of deleting to preserve relationships.
    """
    user = await user_crud.get(db, id=id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Enforce state restriction for state admins
    if current_user.user_type == "ADMINSEMSASUSER" and current_user.state_id != user.state_id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to disable users from other states"
        )
        
    user.is_active = False
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return {
        "success": True,
        "message": "User successfully disabled",
        "data": user
    }

@router.patch("/{id}", response_model=ResponseBase[UserSchema], summary="Edit User")
async def update_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: UUID,
    user_in: UserUpdate,
    current_user: User = Depends(deps.PermissionChecker(["SUPERADMINISTRATOR", "ADMINSEMSASUSER"])),
):
    """
    Update a user's details.
    - SUPERADMINISTRATOR can update any user.
    - ADMINSEMSASUSER can only update users belonging to their own state, and cannot change user state to another state.
    """
    user = await user_crud.get(db, id=id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Enforce state restriction for state admins
    if current_user.user_type == "ADMINSEMSASUSER":
        if current_user.state_id != user.state_id:
            raise HTTPException(
                status_code=403,
                detail="You are not authorized to edit users from other states"
            )
        # Enforce that state admin cannot change the user's state to a different state
        if user_in.state_id is not None and user_in.state_id != current_user.state_id:
            raise HTTPException(
                status_code=403,
                detail=f"You can only assign users to your own state (ID: {current_user.state_id})"
            )
            
    # Check email uniqueness if email is being updated
    if user_in.email is not None and user_in.email != user.email:
        existing_user_email = await user_crud.get_by_email(db, email=user_in.email)
        if existing_user_email:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "User update failed",
                    "error": f"A user with email '{user_in.email}' already exists"
                }
            )

    # Check username uniqueness if username is being updated
    if user_in.user_name is not None and user_in.user_name != user.user_name:
        existing_user_name = await user_crud.get_by_username(db, user_name=user_in.user_name)
        if existing_user_name:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "User update failed",
                    "error": f"A user with username '{user_in.user_name}' already exists"
                }
            )

    updated_user = await user_crud.update(db, db_obj=user, obj_in=user_in)
    return {
        "success": True,
        "message": "User successfully updated",
        "data": updated_user
    }

