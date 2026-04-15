from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.base import get_db
from src.schemas.reference import (
    State, LGA, Drug, DrugCreate, DrugUpdate, 
    StateWithLGAs, AmbulanceType, AmbulanceTypeCreate,
    AccreditationCategory, AccreditationCategoryCreate
)
from src.db.models.reference import State as DBState, LGA as DBLGA, Drug as DBDrug, AmbulanceType as DBAmbType, AccreditationCategory as DBAccCat
from src.services.reference import reference_service
from src.api import deps
from src.db.models.user import User
from src.core.rbac import Permission as PermissionEnum

router = APIRouter()

@router.get("/states", response_model=List[State])
async def read_states(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get all states.
    """
    result = await db.execute(select(DBState).order_by(DBState.name))
    return result.scalars().all()

@router.get("/states-lgas", response_model=List[StateWithLGAs])
async def read_state_lga_hierarchy(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get complete hierarchy of Nigerian states and LGAs for app sync.
    """
    return await reference_service.get_state_lga_hierarchy(db)

@router.get("/states/{state_id}/lgas", response_model=List[LGA])
async def read_state_lgas(
    state_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get all LGAs for a state.
    """
    result = await db.execute(select(DBLGA).where(DBLGA.state_id == state_id).order_by(DBLGA.name))
    return result.scalars().all()

@router.get("/drugs", response_model=List[Drug])
async def read_drugs(
    db: AsyncSession = Depends(get_db),
    query: str = None,
    include_inactive: bool = False
) -> Any:
    """
    Get drug list. (Crew, Admins)
    """
    stmt = select(DBDrug)
    if not include_inactive:
        stmt = stmt.where(DBDrug.is_active == True)
    if query:
        stmt = stmt.where(DBDrug.name.ilike(f"%{query}%"))
    result = await db.execute(stmt.order_by(DBDrug.name))
    return result.scalars().all()

@router.post("/drugs", response_model=Drug)
async def create_drug(
    *,
    db: AsyncSession = Depends(get_db),
    drug_in: DrugCreate,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.REFERENCE_MANAGE]))
) -> Any:
    """
    Add a new drug to the system. (Admins only)
    """
    return await reference_service.create_drug(db, obj_in=drug_in, user_id=current_user.id)

@router.patch("/drugs/{id}", response_model=Drug)
async def update_drug(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    drug_in: DrugUpdate,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.REFERENCE_MANAGE]))
) -> Any:
    """
    Update or deactivate a drug. (Admins only)
    """
    drug = await reference_service.update_drug(db, drug_id=id, obj_in=drug_in, user_id=current_user.id)
    if not drug:
        raise HTTPException(status_code=404, detail="Drug not found")
    return drug

@router.get("/ambulance-types", response_model=List[AmbulanceType])
async def read_ambulance_types(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get all configured ambulance types.
    """
    result = await db.execute(select(DBAmbType).where(DBAmbType.is_active == True).order_by(DBAmbType.name))
    return result.scalars().all()

@router.post("/ambulance-types", response_model=AmbulanceType)
async def create_ambulance_type(
    *,
    db: AsyncSession = Depends(get_db),
    type_in: AmbulanceTypeCreate,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.REFERENCE_MANAGE]))
) -> Any:
    """
    Add a new ambulance type. (Admins only)
    """
    return await reference_service.create_ambulance_type(db, obj_in=type_in, user_id=current_user.id)

@router.get("/accreditation-categories", response_model=List[AccreditationCategory])
async def read_accreditation_categories(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get all configured accreditation categories.
    """
    result = await db.execute(select(DBAccCat).where(DBAccCat.is_active == True).order_by(DBAccCat.name))
    return result.scalars().all()

@router.post("/accreditation-categories", response_model=AccreditationCategory)
async def create_accreditation_category(
    *,
    db: AsyncSession = Depends(get_db),
    cat_in: AccreditationCategoryCreate,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([PermissionEnum.REFERENCE_MANAGE]))
) -> Any:
    """
    Add a new accreditation category. (Admins only)
    """
    return await reference_service.create_accreditation_category(db, obj_in=cat_in, user_id=current_user.id)
