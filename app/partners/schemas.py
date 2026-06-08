from typing import Any, List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import date, datetime

# Generic / Shared
class IdNameSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

class AddedBySchema(BaseModel):
    id: int
    firstName: str = Field(..., alias="first_name")
    lastName: str = Field(..., alias="last_name")
    middleName: Optional[str] = Field("", alias="middle_name")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

# Auth Schemas
class PartnerRegister(BaseModel):
    first_name: str
    middle_name: Optional[str] = ""
    last_name: str
    email: EmailStr
    password: str
    phone_number: Optional[str] = None
    organisation_name: Optional[str] = None
    user_type: Optional[str] = Field("organization", alias="userType")

class PartnerLogin(BaseModel):
    email: EmailStr
    password: str

class PartnerUserResponse(BaseModel):
    id: int
    first_name: str
    middle_name: Optional[str] = ""
    last_name: str
    email: str
    phone_number: Optional[str] = None
    organisation_name: Optional[str] = None
    user_type: Optional[str] = Field("organization", alias="userType")
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PartnerToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    status: str = "success"
    message: str = "Login successful"
    expires_in: int
    user: PartnerUserResponse

# Pledge Schemas
class PartnerPledgeCreate(BaseModel):
    contact_details: Optional[str] = None
    donor_name: Optional[str] = None
    pledge_type: Optional[str] = None # "donation", "investment"
    number_of_ambulance: int = 0
    ambulance_type_id: Optional[int] = None
    state_id: Optional[int] = None
    lga_id: Optional[int] = None
    ward_id: Optional[int] = None
    facility_id: Optional[int] = None
    pledge_date: Optional[datetime] = None
    delivery_date: Optional[datetime] = None
    status: Optional[str] = "pending"

class PartnerPledgeResponse(BaseModel):
    id: int
    pledgeId: str
    contactDetails: Optional[str] = None
    donorName: Optional[str] = None
    pledgeType: Optional[str] = None
    numberOfAmbulance: int
    ambulanceType: Optional[IdNameSchema] = None
    ward: Optional[IdNameSchema] = None
    state: Optional[IdNameSchema] = None
    lga: Optional[IdNameSchema] = None
    facility: Optional[IdNameSchema] = None
    pledgeDate: Optional[str] = None
    deliveryDate: Optional[str] = None
    status: str
    dateAdded: str
    addedBy: AddedBySchema

class PledgeSummary(BaseModel):
    total: int
    pending: int
    fulfilled: int
    notFulfilled: int

class PledgesListData(BaseModel):
    data: List[PartnerPledgeResponse]

class PledgesListContainer(BaseModel):
    summary: PledgeSummary
    list: PledgesListData

class PartnerPledgesListResponse(BaseModel):
    success: bool = True
    message: str = "Fetched successfully"
    data: PledgesListContainer

# Facility Schemas
class PartnerFacilityCreate(BaseModel):
    facility_name: Optional[str] = None
    facility_type: Optional[str] = None # "PHC", "SHC"
    facility_location: Optional[str] = None # "urban", "rural"
    ownership_type: Optional[str] = None # "private", "public"
    communication_devices: List[str] = []
    number_of_ambulance: int = 0
    address: Optional[str] = None
    contact_information: Optional[str] = None
    state_id: Optional[int] = None
    lga_id: Optional[int] = None
    ward_id: Optional[int] = None

class PartnerFacilityResponse(BaseModel):
    id: int
    facilityId: str
    facilityName: Optional[str] = None
    facilityType: Optional[str] = None
    facilityLocation: Optional[str] = None
    ownershipType: Optional[str] = None
    communicationDevices: List[str] = []
    numberOfAmbulance: int
    facilityAddress: Optional[str] = None
    facilityContactInformation: Optional[str] = None
    state: Optional[IdNameSchema] = None
    lga: Optional[IdNameSchema] = None
    ward: Optional[IdNameSchema] = None
    status: str
    dateAdded: str
    addedBy: AddedBySchema

class PaginationSchema(BaseModel):
    total: int
    page: int
    limit: int
    nextPage: Optional[int] = None
    prevPage: Optional[int] = None

class FacilitiesContainer(BaseModel):
    data: List[PartnerFacilityResponse]
    pagination: PaginationSchema

class PartnerFacilitiesListResponse(BaseModel):
    success: bool = True
    message: str = "Fetched successfully"
    data: FacilitiesContainer

# Ambulance Schemas
class PartnerAmbulanceCreate(BaseModel):
    plate_number: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    accreditation_type: Optional[str] = None
    state_id: Optional[int] = None
    lga_id: Optional[int] = None
    ward_id: Optional[int] = None
    facility_id: Optional[int] = None
    vehicle_ownership_type: Optional[str] = None
    driver_name: Optional[str] = None
    contact_number: Optional[str] = None
    fuel_type: Optional[str] = None
    other_fuel_type_option: Optional[str] = ""
    fuel_capacity: Optional[str] = None
    communication_devices: List[str] = []
    other_communication_device_option: Optional[str] = ""
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    equipments: List[str] = []
    road_worthiness_assessment_date: Optional[datetime] = None
    road_worthiness_status: Optional[str] = None
    last_inspection_date: Optional[datetime] = None
    next_scheduled_maintenance: Optional[datetime] = None
    inspection_notes: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_expiration_date: Optional[datetime] = None

class AmbBasicInformation(BaseModel):
    plateNumber: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    accreditationType: Optional[str] = None
    state: Optional[IdNameSchema] = None
    lga: Optional[IdNameSchema] = None
    ward: Optional[IdNameSchema] = None
    facility: Optional[IdNameSchema] = None
    vehicleOwnershipType: Optional[str] = None
    driverName: Optional[str] = None
    contactNumber: Optional[str] = None
    createdAt: str
    updatedAt: str

class AmbTechnicalSpecification(BaseModel):
    fuelType: Optional[str] = None
    otherFuelTypeOption: Optional[str] = ""
    fuelCapicity: Optional[str] = None # note: matching spelling from JSON 'fuelCapicity'
    communicationDevices: List[str] = []
    otherCommunicationDeviceOption: Optional[str] = ""
    latitude: Optional[str] = None
    longitude: Optional[str] = None

class AmbEquipmentInventory(BaseModel):
    equipments: List[str] = []

class AmbComplianceAndDocumentation(BaseModel):
    roadWorthinessAssessmentDate: Optional[str] = None
    roadWorthinessStatus: Optional[str] = None
    lastInspectionDate: Optional[str] = None
    nextScheduledMaintenance: Optional[str] = None
    inspectionNotes: Optional[str] = None
    insuranceProvider: Optional[str] = None
    insuranceExpirationDate: Optional[str] = None

class AmbStatus(BaseModel):
    status: str
    isOutForMaintenance: bool
    isOutOfService: bool

class PartnerAmbulanceResponse(BaseModel):
    id: int
    ambulanceId: str
    basicInformation: AmbBasicInformation
    technicalSpecification: AmbTechnicalSpecification
    equipmentInventory: AmbEquipmentInventory
    complianceAndDocumentation: AmbComplianceAndDocumentation
    documents: dict = {}
    status: AmbStatus

class AmbulanceListSummary(BaseModel):
    total: int
    active: int
    outOfService: int
    outForMaintenance: int

class AmbulancesContainer(BaseModel):
    data: List[PartnerAmbulanceResponse]
    pagination: PaginationSchema

class AmbulancesListContainer(BaseModel):
    ambulances: AmbulancesContainer
    ambulanceSummary: AmbulanceListSummary

class PartnerAmbulancesListResponse(BaseModel):
    success: bool = True
    message: str = "Fetched successfully"
    data: AmbulancesListContainer

# Dashboard / Overview schemas
class AmbOverviewItem(BaseModel):
    id: str
    plateNumber: Optional[str] = None
    driverName: Optional[str] = None
    state: Optional[str] = None
    lga: Optional[str] = None
    ward: Optional[str] = None
    facility: Optional[str] = None
    isOutForMaintenance: bool
    isOutOfService: bool
    vehicleOwnershipType: Optional[str] = None
    status: str
    createdAt: str
    updatedAt: str

class OverviewCardAmbulance(BaseModel):
    total: int
    statusCounts: dict # {"active": x, "under_maintenance": y, "out_of_service": z}
    ownershipCounts: dict # {"private": x, "public": y}

class OverviewCardHealthFacility(BaseModel):
    total: int
    ownershipType: dict # {"public": x, "private": y}
    facilityLocation: dict # {"urban": x, "rural": y}

class OverviewCardRequired(BaseModel):
    requiredAmbulances: int
    coveragePercentage: float
    gapPercentage: float

class OverviewCardGaps(BaseModel):
    gapCount: int
    coveragePercentage: float
    gapPercentage: float

class OverviewCardsContainer(BaseModel):
    ambulance: OverviewCardAmbulance
    healthFacility: OverviewCardHealthFacility
    required: OverviewCardRequired
    gaps: OverviewCardGaps

class OverviewListData(BaseModel):
    data: List[AmbOverviewItem]
    pagination: PaginationSchema

class DashboardOverviewContainer(BaseModel):
    overViewList: OverviewListData
    overViewCards: OverviewCardsContainer

class PartnerDashboardResponse(BaseModel):
    success: bool = True
    message: str = "Fetched successfully"
    data: DashboardOverviewContainer
