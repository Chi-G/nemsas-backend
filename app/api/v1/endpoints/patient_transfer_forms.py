from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import extract
from app.api import deps
from app.schemas.transfer_form import (
    TransferFormBindingModel, 
    TransferFormUpdateBindingModel, 
    TransferFormModel,
    CustomRequiredIdModel
)
from app.models.transfer_form import TransferForm
from app.models.run_sheet import RunSheet
from app.crud.transfer_form import transfer_form as crud_transfer_form

router = APIRouter()

@router.post("/add", response_model=Any)
async def add_transfer_form(
    *,
    db: AsyncSession = Depends(deps.get_db),
    obj_in: TransferFormBindingModel,
    current_user = Depends(deps.get_current_user)
) -> Any:
    """
    Create a new Transfer Form.
    """
    db_obj = await crud_transfer_form.create(db, obj_in=obj_in)
    return {
        "success": True,
        "message": "Transfer Form successfully created",
        "data": TransferFormModel.model_validate(db_obj)
    }

@router.delete("/delete", response_model=Any)
async def delete_transfer_form(
    *,
    db: AsyncSession = Depends(deps.get_db),
    payload: CustomRequiredIdModel,
    current_user = Depends(deps.get_current_user)
) -> Any:
    """
    Delete a Transfer Form by ID.
    """
    db_obj = await crud_transfer_form.remove(db, id=payload.id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfer Form not found"
        )
    return {
        "success": True,
        "message": "Transfer Form successfully deleted"
    }

@router.get("/get", response_model=Any)
async def get_transfer_forms(
    *,
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    incident_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    etc_id: Optional[int] = None,
    run_sheet_id: Optional[int] = None,
    current_user = Depends(deps.get_current_user)
) -> Any:
    """
    Get all Transfer Forms with optional filtering and pagination.
    """
    items, total = await crud_transfer_form.get_multi_with_count(
        db,
        skip=skip,
        limit=limit,
        incident_id=incident_id,
        patient_id=patient_id,
        etc_id=etc_id,
        run_sheet_id=run_sheet_id
    )
    return {
        "success": True,
        "message": "Transfer Forms successfully fetched",
        "data": {"items": [TransferFormModel.model_validate(item) for item in items]},
        "totalCount": total
    }

@router.post("/getByAssignedAmbulance", response_model=Any)
async def get_by_assigned_ambulance(
    *,
    db: AsyncSession = Depends(deps.get_db),
    payload: CustomRequiredIdModel,
    current_user = Depends(deps.get_current_user)
) -> Any:
    """
    Get Transfer Forms assigned to a specific ambulance.
    """
    # Join run_sheets to match ambulance_id
    stmt = select(TransferForm).join(TransferForm.run_sheet).where(RunSheet.ambulance_id == payload.id)
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return {
        "success": True,
        "message": "Transfer Forms successfully fetched for ambulance",
        "data": {"items": [TransferFormModel.model_validate(item) for item in items]},
        "totalCount": len(items)
    }

@router.post("/getByAssignedETC", response_model=Any)
async def get_by_assigned_etc(
    *,
    db: AsyncSession = Depends(deps.get_db),
    payload: CustomRequiredIdModel,
    year: Optional[int] = None,
    month: Optional[int] = None,
    current_user = Depends(deps.get_current_user)
) -> Any:
    """
    Get Transfer Forms assigned to a specific ETC, with optional year and month filters.
    """
    stmt = select(TransferForm).where(TransferForm.etc_id == payload.id)
    if year is not None:
        stmt = stmt.where(extract('year', TransferForm.created_at) == year)
    if month is not None:
        stmt = stmt.where(extract('month', TransferForm.created_at) == month)
        
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return {
        "success": True,
        "message": "Transfer Forms successfully fetched for ETC",
        "data": {"items": [TransferFormModel.model_validate(item) for item in items]},
        "totalCount": len(items)
    }

@router.post("/getSingle", response_model=Any)
async def get_single_transfer_form(
    *,
    db: AsyncSession = Depends(deps.get_db),
    payload: CustomRequiredIdModel,
    current_user = Depends(deps.get_current_user)
) -> Any:
    """
    Get a single Transfer Form by ID.
    """
    db_obj = await crud_transfer_form.get(db, payload.id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfer Form not found"
        )
    return {
        "success": True,
        "message": "Transfer Form successfully fetched",
        "data": TransferFormModel.model_validate(db_obj)
    }

@router.put("/update", response_model=Any)
async def update_transfer_form(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
    obj_in: TransferFormUpdateBindingModel,
    current_user = Depends(deps.get_current_user)
) -> Any:
    """
    Update a Transfer Form.
    """
    db_obj = await crud_transfer_form.get(db, id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfer Form not found"
        )
    updated_obj = await crud_transfer_form.update(db, db_obj=db_obj, obj_in=obj_in)
    return {
        "success": True,
        "message": "Transfer Form successfully updated",
        "data": TransferFormModel.model_validate(updated_obj)
    }
