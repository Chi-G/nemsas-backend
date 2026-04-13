from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import deps
from src.db.base import get_db
from src.schemas.run_sheet import RunSheet, RunSheetUpdate, RunSheetDrug
from src.schemas.reference import Drug
from src.services.run_sheet import run_sheet_service
from src.db.models.user import User
from src.core.rbac import Permission

router = APIRouter()

@router.get("/drugs", response_model=List[Drug])
async def search_drugs(
    *,
    db: AsyncSession = Depends(get_db),
    q: Optional[str] = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Search available drugs for run sheet entry.
    """
    return await run_sheet_service.get_drug_list(db, query=q)

@router.get("/by-incident/{incident_id}", response_model=RunSheet)
async def get_run_sheet_by_incident(
    *,
    db: AsyncSession = Depends(get_db),
    incident_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get run sheet associated with an incident.
    """
    # Logic to check permission or owner if needed
    run_sheet = await run_sheet_service.get_by_incident_id(db, incident_id=incident_id)
    if not run_sheet:
        raise HTTPException(status_code=404, detail="Run sheet not found for this incident")
    return run_sheet

@router.get("/{run_sheet_id}", response_model=RunSheet)
async def get_run_sheet(
    *,
    db: AsyncSession = Depends(get_db),
    run_sheet_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get detailed run sheet.
    """
    run_sheet = await run_sheet_service.get_by_id(db, run_sheet_id=run_sheet_id)
    if not run_sheet:
        raise HTTPException(status_code=404, detail="Run sheet not found")
    return run_sheet

@router.post("/{run_sheet_id}/save", response_model=RunSheet)
async def save_run_sheet(
    *,
    db: AsyncSession = Depends(get_db),
    run_sheet_id: int,
    run_sheet_in: RunSheetUpdate,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([Permission.INCIDENT_MANAGE])),
) -> Any:
    """
    Progressive save of run sheet data. Records history snapshot.
    """
    try:
        return await run_sheet_service.progressive_save(
            db, run_sheet_id=run_sheet_id, obj_in=run_sheet_in, user_id=current_user.id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{run_sheet_id}/sign", response_model=RunSheet)
async def sign_run_sheet(
    *,
    db: AsyncSession = Depends(get_db),
    run_sheet_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    _: Any = Depends(deps.PermissionChecker([Permission.INCIDENT_MANAGE])),
) -> Any:
    """
    Apply crew electronic signature and lock the record.
    """
    try:
        # Verify if the user is part of the crew or has authority
        # For simplicity, we assume crew has INCIDENT_MANAGE
        return await run_sheet_service.sign_by_crew(
            db, run_sheet_id=run_sheet_id, user_id=current_user.id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
