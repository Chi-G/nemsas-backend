from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.crud.medical_intervention import medical_intervention_crud
from app.schemas.medical_intervention import MedicalIntervention, MedicalInterventionCreate, MedicalInterventionUpdate

router = APIRouter()

@router.get("/", response_model=List[MedicalIntervention])
async def read_medical_interventions(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    patient_id: Optional[int] = Query(None),
) -> Any:
    """
    Retrieve medical interventions.
    """
    interventions = await medical_intervention_crud.get_multi(
        db, skip=skip, limit=limit, patient_id=patient_id
    )
    return interventions

@router.post("/", response_model=MedicalIntervention)
async def create_medical_intervention(
    *,
    db: AsyncSession = Depends(deps.get_db),
    intervention_in: MedicalInterventionCreate,
) -> Any:
    """
    Create new medical intervention.
    """
    intervention = await medical_intervention_crud.create(db, obj_in=intervention_in)
    return intervention

@router.put("/{id}", response_model=MedicalIntervention)
async def update_medical_intervention(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
    intervention_in: MedicalInterventionUpdate,
) -> Any:
    """
    Update a medical intervention.
    """
    intervention = await medical_intervention_crud.get(db, id=id)
    if not intervention:
        raise HTTPException(status_code=404, detail="Medical intervention not found")
    intervention = await medical_intervention_crud.update(
        db, db_obj=intervention, obj_in=intervention_in
    )
    return intervention

@router.get("/{id}", response_model=MedicalIntervention)
async def read_medical_intervention(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
) -> Any:
    """
    Get medical intervention by ID.
    """
    intervention = await medical_intervention_crud.get(db, id=id)
    if not intervention:
        raise HTTPException(status_code=404, detail="Medical intervention not found")
    return intervention

@router.delete("/{id}", response_model=MedicalIntervention)
async def delete_medical_intervention(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
) -> Any:
    """
    Delete a medical intervention.
    """
    intervention = await medical_intervention_crud.get(db, id=id)
    if not intervention:
        raise HTTPException(status_code=404, detail="Medical intervention not found")
    intervention = await medical_intervention_crud.remove(db, id=id)
    return intervention
