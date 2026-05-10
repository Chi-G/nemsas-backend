from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.schemas.state import State
from app.schemas.lga import LGA
from app.schemas.ward import Ward

class UserBase(BaseModel):
    first_name: str = Field(..., alias="firstName")
    middle_name: Optional[str] = Field("", alias="middleName")
    last_name: str = Field(..., alias="lastName")
    user_name: str = Field(..., alias="userName")
    email: str
    phone_number: Optional[str] = Field(None, alias="phoneNumber")
    sex: Optional[int] = None
    street1: Optional[str] = None
    street2: Optional[str] = None
    city: Optional[str] = None
    is_active: bool = Field(True, alias="isActive")
    profile_picture: Optional[str] = Field(None, alias="profilePicture")
    is_password_changed: bool = Field(False, alias="isPasswordChanged")

    user_type: Optional[str] = Field(None, alias="userType")
    real_user_type: Optional[str] = Field(None, alias="realUserType")
    organisation_name: Optional[str] = Field(None, alias="organisationName")
    supervisor_user_id: Optional[str] = Field(None, alias="supervisorUserId")
    emergency_treatment_center_id: Optional[int] = Field(None, alias="emergencyTreatmentCenterId")
    etc_id: Optional[int] = Field(None, alias="etcId")
    ambulance_id: Optional[int] = Field(None, alias="ambulanceId")
    state_id: Optional[int] = Field(None, alias="stateId")
    lga_id: Optional[int] = Field(None, alias="lgaId")
    ward_id: Optional[int] = Field(None, alias="wardId")

    @model_validator(mode='after')
    def sync_etc_ids(self) -> 'UserBase':
        if self.etc_id is not None and self.emergency_treatment_center_id is None:
            self.emergency_treatment_center_id = self.etc_id
        elif self.emergency_treatment_center_id is not None and self.etc_id is None:
            self.etc_id = self.emergency_treatment_center_id
        return self

    class Config:
        populate_by_name = True
        from_attributes = True

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., alias="currentPassword")
    new_password: str = Field(..., alias="newPassword")

class User(UserBase):
    id: UUID
    date_joined: datetime = Field(..., alias="dateJoined")
    state: Optional[State] = None
    lga: Optional[LGA] = None
    ward: Optional[Ward] = None
