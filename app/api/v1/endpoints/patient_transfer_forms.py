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

@router.get("/etcTransferForms", response_model=Any)
async def get_etc_transfer_forms_for_user(
    skip: int = 0,
    limit: int = 100,
    month: Optional[int] = None,
    year: Optional[int] = None,
    status: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
) -> Any:
    """
    Get Transfer Forms for the logged-in ETC user, fully hydrated with patient names and incident metadata.
    """
    user_type = getattr(current_user, "user_type", None)
    if user_type != "EMERGENCYTREATMENTUSER":
        raise HTTPException(status_code=403, detail="Only EMERGENCYTREATMENTUSER can access this endpoint")
        
    etc_id = getattr(current_user, "etc_id", None) or getattr(current_user, "emergency_treatment_center_id", None)
    if not etc_id:
        raise HTTPException(status_code=403, detail="User is not assigned to any ETC")

    from sqlalchemy.orm import selectinload
    from app.models.incident import Incident
    from app.models.hospital import Hospital
    from app.models.patient import Patient
    from sqlalchemy import func, extract, or_
    
    stmt = select(TransferForm).where(
        TransferForm.etc_id == etc_id
    )
    count_stmt = select(func.count(TransferForm.id)).where(TransferForm.etc_id == etc_id)

    if month is not None:
        stmt = stmt.where(extract('month', TransferForm.created_at) == month)
        count_stmt = count_stmt.where(extract('month', TransferForm.created_at) == month)
        
    if year is not None:
        stmt = stmt.where(extract('year', TransferForm.created_at) == year)
        count_stmt = count_stmt.where(extract('year', TransferForm.created_at) == year)
        
    if status is not None:
        stmt = stmt.where(TransferForm.approve == status)
        count_stmt = count_stmt.where(TransferForm.approve == status)
        
    if search:
        search_term = f"%{search}%"
        search_filter = TransferForm.incident.has(
            Incident.patients.any(
                or_(
                    Patient.first_name.ilike(search_term),
                    Patient.last_name.ilike(search_term),
                    Patient.middle_name.ilike(search_term)
                )
            )
        )
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    stmt = stmt.options(
        selectinload(TransferForm.incident).selectinload(Incident.patients),
        selectinload(TransferForm.incident).selectinload(Incident.ambulance),
        selectinload(TransferForm.incident).selectinload(Incident.state),
        selectinload(TransferForm.hospital).selectinload(Hospital.state)
    ).order_by(TransferForm.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    forms = result.scalars().all()
    
    response_data = []
    for form in forms:
        incident = form.incident
        
        # Determine patient names
        patient_names = []
        patient_ids = form.patient_ids or []
        if not patient_ids and form.patient_id:
            patient_ids = [form.patient_id]
            
        if incident and incident.patients:
            for p in incident.patients:
                if not patient_ids or p.id in patient_ids:
                    parts = filter(None, [p.first_name, p.last_name])
                    patient_names.append(" ".join(parts))
        
        etc_name = form.hospital.name if form.hospital else "Unknown ETC"
        
        state_name = None
        if form.hospital and form.hospital.state:
            state_name = form.hospital.state.name
        elif incident and incident.state:
            state_name = incident.state.name
            
        ambulance_name = None
        if incident and incident.ambulance:
            ambulance_name = incident.ambulance.name
            
        arrival_time = incident.ambulance_stop if incident else form.created_at
        
        status = incident.incident_status_type if incident else None
        triage_category = incident.triage_category if incident else None
        
        response_data.append({
            "id": form.id,
            "incidentId": form.incident_id,
            "patientNames": patient_names,
            "etcName": etc_name,
            "stateName": state_name,
            "ambulanceName": ambulance_name,
            "arrivalTime": arrival_time,
            "status": status,
            "triageCategory": triage_category,
            "approve": form.approve,
            "createdAt": form.created_at
        })
        
    # Get total count
    total_count = (await db.execute(count_stmt)).scalar()
        
    return {
        "success": True,
        "message": "ETC Transfer Forms fetched successfully",
        "data": response_data,
        "totalCount": total_count
    }
@router.get("/{id}", response_model=Any)
async def get_single_transfer_form(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
    current_user = Depends(deps.get_current_user)
) -> Any:
    """
    Get a single Transfer Form by ID.
    """
    from sqlalchemy.orm import selectinload
    from app.models.incident import Incident
    from app.models.hospital import Hospital
    from app.models.user import User
    
    stmt = select(TransferForm).where(TransferForm.id == id).options(
        selectinload(TransferForm.incident).selectinload(Incident.patients),
        selectinload(TransferForm.incident).selectinload(Incident.ambulance),
        selectinload(TransferForm.hospital),
        selectinload(TransferForm.hospice_user)
    )
    result = await db.execute(stmt)
    db_obj = result.scalar_one_or_none()
    
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfer Form not found"
        )
        
    incident = db_obj.incident
    patient_ids = db_obj.patient_ids or []
    if not patient_ids and db_obj.patient_id:
        patient_ids = [db_obj.patient_id]
        
    patients_data = []
    if incident and incident.patients:
        for p in incident.patients:
            if not patient_ids or p.id in patient_ids:
                patients_data.append({
                    "firstName": p.first_name,
                    "middleName": p.middle_name,
                    "lastName": p.last_name
                })
                
    ambulance_name = incident.ambulance.name if incident and incident.ambulance else None
    etc_name = db_obj.hospital.name if db_obj.hospital else None
    
    hospice_user_data = None
    if db_obj.hospice_user:
        hospice_user_data = {
            "id": str(db_obj.hospice_user.id),
            "firstName": getattr(db_obj.hospice_user, "first_name", ""),
            "lastName": getattr(db_obj.hospice_user, "last_name", ""),
            "email": getattr(db_obj.hospice_user, "email", "")
        }
        
    arrival_time = incident.ambulance_stop if incident else db_obj.created_at
        
    response_data = {
        **TransferFormModel.model_validate(db_obj).model_dump(by_alias=True),
        "patients": patients_data,
        "ambulanceName": ambulance_name,
        "etcName": etc_name,
        "arrivalTime": arrival_time,
        "hospiceUser": hospice_user_data
    }

    return {
        "success": True,
        "message": "Transfer Form successfully fetched",
        "data": response_data
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
    if obj_in.approve is not None:
        db_obj.hospice_user_id = getattr(current_user, "id", None)
        
    updated_obj = await crud_transfer_form.update(db, db_obj=db_obj, obj_in=obj_in)
    return {
        "success": True,
        "message": "Transfer Form successfully updated",
        "data": TransferFormModel.model_validate(updated_obj)
    }

