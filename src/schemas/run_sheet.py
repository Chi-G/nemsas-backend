from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional
from src.db.models.run_sheet import RunSheetStatus

class RunSheetDrugBase(BaseModel):
    drug_id: Optional[int] = None
    custom_drug_name: Optional[str] = None
    dosage: str
    administered_at: Optional[datetime] = None
    is_reimbursable: bool = True

class RunSheetDrugCreate(RunSheetDrugBase):
    pass

class RunSheetDrug(RunSheetDrugBase):
    id: int
    run_sheet_id: int

    model_config = ConfigDict(from_attributes=True)

class RunSheetBase(BaseModel):
    patient_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    chief_complaint: Optional[str] = None
    assessment: Optional[str] = None
    blood_pressure: Optional[str] = None
    pulse_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None
    temperature: Optional[float] = None
    gcs: Optional[int] = None

class RunSheetCreate(BaseModel):
    incident_id: int
    dispatch_id: int

class RunSheetUpdate(RunSheetBase):
    drug_entries: Optional[List[RunSheetDrugCreate]] = None
    model_config = ConfigDict(from_attributes=True)

class RunSheet(RunSheetBase):
    id: int
    incident_id: int
    dispatch_id: int
    status: RunSheetStatus
    crew_signature_id: Optional[int] = None
    crew_signed_at: Optional[datetime] = None
    etc_signature_id: Optional[int] = None
    etc_signed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    drug_entries: List[RunSheetDrug] = []

    model_config = ConfigDict(from_attributes=True)

class RunSheetHistory(BaseModel):
    id: int
    run_sheet_id: int
    data_snapshot: dict
    saved_at: datetime
    saved_by_id: int

    model_config = ConfigDict(from_attributes=True)
