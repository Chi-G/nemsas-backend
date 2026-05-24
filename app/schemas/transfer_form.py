from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional
from uuid import UUID

class TransferFormBindingModel(BaseModel):
    incident_id: int = Field(..., alias="incidentId")
    medic_user_id: Optional[UUID] = Field(None, alias="medicUserId")
    hospice_user_id: Optional[UUID] = Field(None, alias="hospiceUserId")
    patient_id: int = Field(..., alias="patient_Id")
    etc_id: int = Field(..., alias="etC_Id")
    run_sheet_id: int = Field(..., alias="runSheetId")
    approve: Optional[bool] = Field(False, alias="approve")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class TransferFormUpdateBindingModel(BaseModel):
    approve: Optional[bool] = Field(None, alias="approve")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class TransferFormModel(BaseModel):
    id: int
    incident_id: int = Field(..., alias="incidentId")
    medic_user_id: Optional[UUID] = Field(None, alias="medicUserId")
    hospice_user_id: Optional[UUID] = Field(None, alias="hospiceUserId")
    patient_id: int = Field(..., alias="patient_Id")
    etc_id: int = Field(..., alias="etC_Id")
    run_sheet_id: int = Field(..., alias="runSheetId")
    approve: Optional[bool] = Field(None, alias="approve")
    created_at: Optional[datetime] = Field(None, alias="created_at")
    updated_at: Optional[datetime] = Field(None, alias="updated_at")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class CustomRequiredIdModel(BaseModel):
    id: int = Field(..., alias="id")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
