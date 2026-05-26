from typing import Any, Optional, List, cast
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.models.user import User
from app.schemas.claim import ClaimPaginatedResponse, ClaimResponse, ClaimCreate, ClaimSummaryResponse
from app.crud.claim import claim as crud_claim
from app.crud.claim_setting import claim_setting as crud_setting
from app.schemas.claim_setting import ClaimSetting
from fastapi import UploadFile, File
import cloudinary
import cloudinary.uploader
from app.core.config import settings
from sqlalchemy.future import select
from app.models.run_sheet import RunSheet
from app.models.patient import Patient
from app.models.incident import Incident
from pydantic import BaseModel, ConfigDict, Field, model_validator

router = APIRouter()

@router.post("/upload")
async def upload_claim_image(
    request: Request,
    file: UploadFile = File(...)
) -> Any:
    """
    Upload an image/receipt to Cloudinary or local storage and return the URL.
    """
    # Check if Cloudinary should be used
    use_cloudinary = settings.UPLOAD_PROVIDER.lower() == "cloudinary"
    
    # Check if Cloudinary credentials are fully configured
    if use_cloudinary:
        if not all([settings.CLOUDINARY_CLOUD_NAME, settings.CLOUDINARY_API_KEY, settings.CLOUDINARY_API_SECRET]):
            print("[Upload] Cloudinary credentials missing. Falling back to local upload.")
            use_cloudinary = False
            
    contents = await file.read()
    url = None
    message = ""
    
    if use_cloudinary:
        try:
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET,
                secure=True
            )
            upload_result = cloudinary.uploader.upload(contents)
            url = upload_result.get("secure_url")
            message = "File successfully uploaded to Cloudinary"
        except Exception as e:
            print(f"[Upload] Cloudinary upload failed: {e}. Falling back to local upload.")
            use_cloudinary = False
            
    if not use_cloudinary:
        # Local upload logic
        import uuid
        import os
        
        # Ensure uploads folder exists in local context
        upload_dir = "static/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate a unique safe filename
        safe_filename = f"{uuid.uuid4().hex}_{os.path.basename(file.filename or 'upload.jpg')}"
        file_path = os.path.join(upload_dir, safe_filename)
        
        # Write file content locally
        with open(file_path, "wb") as f:
            f.write(contents)
            
        # Construct absolute URL using incoming request
        base_url = str(request.base_url)
        if not base_url.endswith("/"):
            base_url += "/"
        url = f"{base_url}static/uploads/{safe_filename}"
        message = "File successfully uploaded locally"
        
    return {
        "success": True,
        "message": message,
        "url": url
    }

@router.get("/", response_model=ClaimPaginatedResponse)
async def read_claims(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    query: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    current_user: User = Depends(deps.PermissionChecker(["SUPERADMINISTRATOR", "NEMSASADMIN", "ADMINSEMSASUSER", "NEMSASUSER", "SEMSASUSER"]))
) -> Any:
    """
    Get claims for ambulances or etc.
    Supports standard filtering parameters provided by the user workflow.
    """
    state_id = None
    user_type = getattr(current_user, "user_type", None)
    if user_type in ["ADMINSEMSASUSER", "SEMSASUSER", "SEMSASDISPATCH"]:
        state_id = getattr(current_user, "state_id", None)
        if state_id is None:
            raise HTTPException(status_code=403, detail="State ID is required for state-level users")

    items, total = await crud_claim.get_multi_with_count(
        db,
        skip=skip,
        limit=limit,
        status=status,
        query_review=query,
        year=year,
        month=month,
        state_id=state_id
    )
    return {
        "success": True,
        "message": "Claim(s) successfully fetched",
        "data": {"items": items},
        "totalCount": total
    }

@router.get("/summary", response_model=ClaimSummaryResponse)
async def read_claim_summary(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.PermissionChecker(["SUPERADMINISTRATOR", "NEMSASADMIN", "ADMINSEMSASUSER", "NEMSASUSER", "SEMSASUSER"]))
) -> Any:
    """
    Get aggregated summary counts of all claims.
    """
    state_id = None
    user_type = getattr(current_user, "user_type", None)
    if user_type in ["ADMINSEMSASUSER", "SEMSASUSER", "SEMSASDISPATCH"]:
        state_id = getattr(current_user, "state_id", None)
        if state_id is None:
            raise HTTPException(status_code=403, detail="State ID is required for state-level users")

    summary_data = await crud_claim.get_summary(db, state_id=state_id)
    return {
        "success": True,
        "message": "Claim summary retrieved successfully",
        "data": summary_data,
        "totalCount": 1,
        "refreshToken": None,
        "refreshTokenExpiryTime": "0001-01-01T00:00:00"
    }


@router.get("/ambulance", response_model=ClaimPaginatedResponse)
async def read_ambulance_claims(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    query: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    ambulance_id: Optional[int] = None,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get claims specifically for the signed-in ambulance user or all ambulance claims for administrators.
    """
    user_ambulance_id = getattr(current_user, "ambulance_id", None)
    admin_roles = {"SUPERADMINISTRATOR", "NEMSASADMIN", "ADMINSEMSASUSER", "NEMSASUSER", "SEMSASUSER"}
    user_role = getattr(current_user, "user_type", None)
    is_admin = user_role in admin_roles

    if not is_admin and not user_ambulance_id:
        raise HTTPException(
            status_code=400,
            detail="The current signed-in user is not associated with any ambulance."
        )
    
    # If the user is an ambulance provider, they can only view their own claims.
    # If the user is an admin, they can view all claims or filter by query param ambulance_id.
    filter_ambulance_id = user_ambulance_id if not is_admin else (ambulance_id or user_ambulance_id)
    
    items, total = await crud_claim.get_multi_with_count(
        db,
        skip=skip,
        limit=limit,
        status=status,
        query_review=query,
        year=year,
        month=month,
        ambulance_id=filter_ambulance_id
    )
    return {
        "success": True,
        "message": "Ambulance claim(s) successfully fetched",
        "data": {"items": items},
        "totalCount": total
    }

@router.get("/settings")
async def read_claim_settings(
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Global retrieval of expiration controls and thresholds.
    """
    configs = await crud_setting.get_all(db)
    # Reformat to plain dictionary or list as needed, maintaining client compatibility.
    return configs

@router.post("/", response_model=ClaimResponse)
async def create_claim(
    *,
    db: AsyncSession = Depends(deps.get_db),
    claim_in: ClaimCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create a new claim.
    """
    item = await crud_claim.create(db, obj_in=claim_in, current_user=current_user)
    return {
        "success": True,
        "message": "Claim successfully created",
        "data": item
    }

@router.get("/getAllAmbulance", response_model=ClaimPaginatedResponse)
async def get_all_ambulance_claims(
    db: AsyncSession = Depends(deps.get_db),
    page: int = 1,
    pageSize: int = 10,
    year: Optional[int] = None,
    month: Optional[int] = None,
    stateId: Optional[int] = None,
    status: Optional[str] = None,
    claimQuery: Optional[str] = None,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get all ambulance claims with paginated filters matching legacy API.
    """
    skip = (page - 1) * pageSize
    limit = pageSize

    # Resolve state_id constraint for SEMSAS users
    user_type = getattr(current_user, "user_type", None)
    filter_state_id = stateId
    if user_type in ["ADMINSEMSASUSER", "SEMSASUSER", "SEMSASDISPATCH"]:
        user_state_id = getattr(current_user, "state_id", None)
        if user_state_id is None:
            raise HTTPException(status_code=403, detail="State ID is required for state-level users")
        filter_state_id = user_state_id

    user_ambulance_id = getattr(current_user, "ambulance_id", None)
    admin_roles = {"SUPERADMINISTRATOR", "NEMSASADMIN", "ADMINSEMSASUSER", "NEMSASUSER", "SEMSASUSER"}
    is_admin = user_type in admin_roles

    if not is_admin and not user_ambulance_id:
        raise HTTPException(
            status_code=400,
            detail="The current signed-in user is not associated with any ambulance."
        )

    filter_ambulance_id = user_ambulance_id if not is_admin else None

    items, total = await crud_claim.get_multi_with_count(
        db,
        skip=skip,
        limit=limit,
        status=status,
        query_review=claimQuery,
        year=year,
        month=month,
        is_etc=False,
        ambulance_id=filter_ambulance_id,
        state_id=filter_state_id
    )

    return {
        "success": True,
        "message": "Ambulance claim(s) successfully fetched",
        "data": {"items": items},
        "totalCount": total
    }


@router.get("/getAllETC", response_model=ClaimPaginatedResponse)
async def get_all_etc_claims(
    db: AsyncSession = Depends(deps.get_db),
    page: int = 1,
    pageSize: int = 10,
    year: Optional[int] = None,
    month: Optional[int] = None,
    stateId: Optional[int] = None,
    status: Optional[str] = None,
    claimQuery: Optional[str] = None,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get all ETC claims with paginated filters matching legacy API.
    """
    skip = (page - 1) * pageSize
    limit = pageSize

    user_type = getattr(current_user, "user_type", None)
    filter_state_id = stateId
    if user_type in ["ADMINSEMSASUSER", "SEMSASUSER", "SEMSASDISPATCH"]:
        user_state_id = getattr(current_user, "state_id", None)
        if user_state_id is None:
            raise HTTPException(status_code=403, detail="State ID is required for state-level users")
        filter_state_id = user_state_id

    items, total = await crud_claim.get_multi_with_count(
        db,
        skip=skip,
        limit=limit,
        status=status,
        query_review=claimQuery,
        year=year,
        month=month,
        is_etc=True,
        state_id=filter_state_id
    )

    return {
        "success": True,
        "message": "ETC claim(s) successfully fetched",
        "data": {"items": items},
        "totalCount": total
    }


@router.get("/{id}", response_model=ClaimResponse)
async def read_claim(
    id: int,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    item = await crud_claim.get(db, id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {
        "success": True,
        "message": "Claim successfully fetched",
        "data": item
    }

from datetime import datetime
from app.models.claim import ClaimAuditLog, ClaimAction, ClaimStatus

class ClaimRejectionRequest(BaseModel):
    rejection_reason: str = Field(..., alias="rejectionReason")

    @model_validator(mode='before')
    @classmethod
    def validate_reason(cls, data: Any) -> Any:
        if isinstance(data, dict):
            reason = data.get("rejection_reason") or data.get("rejectionReason")
            if not reason or not str(reason).strip():
                raise ValueError("rejectionReason is mandatory and cannot be empty")
        return data

@router.post("/{id}/approve", response_model=ClaimResponse)
async def approve_claim(
    id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.PermissionChecker(["SUPERADMINISTRATOR", "NEMSASADMIN", "ADMINSEMSASUSER", "NEMSASUSER", "SEMSASUSER"]))
) -> Any:
    claim_obj = await crud_claim.get(db, id=id)
    if not claim_obj:
        raise HTTPException(status_code=404, detail="Claim not found")
        
    user_type = getattr(current_user, "user_type", None)
    if user_type in ["ADMINSEMSASUSER", "SEMSASUSER", "SEMSASDISPATCH"]:
        raise HTTPException(
            status_code=403,
            detail="SEMSAS users cannot directly approve claims. They must endorse them instead."
        )
            
    claim_obj.status = "Approved"  # type: ignore
    claim_obj.processed_at = datetime.now()  # type: ignore
    claim_obj.processed_by_id = current_user.id  # type: ignore
    db.add(claim_obj)
    
    audit_log = ClaimAuditLog(
        claim_id=claim_obj.id,
        action=ClaimAction.APPROVE,
        processed_by_id=current_user.id
    )
    db.add(audit_log)
    
    await db.commit()
    
    updated_item = await crud_claim.get(db, id=id)
    return {
        "success": True,
        "message": "Claim approved successfully",
        "data": updated_item
    }

@router.post("/{id}/reject", response_model=ClaimResponse)
async def reject_claim(
    id: int,
    body: ClaimRejectionRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.PermissionChecker(["SUPERADMINISTRATOR", "NEMSASADMIN", "ADMINSEMSASUSER", "NEMSASUSER", "SEMSASUSER"]))
) -> Any:
    claim_obj = await crud_claim.get(db, id=id)
    if not claim_obj:
        raise HTTPException(status_code=404, detail="Claim not found")
        
    user_type = getattr(current_user, "user_type", None)
    if user_type in ["ADMINSEMSASUSER", "SEMSASUSER", "SEMSASDISPATCH"]:
        if current_user.state_id is None:
            raise HTTPException(status_code=403, detail="State ID is required for state-level users")
        if not claim_obj.incident or claim_obj.incident.state_id != current_user.state_id:
            raise HTTPException(status_code=403, detail="The user doesn't have enough privileges to reject claims in this state")
            
    reason = body.rejection_reason
    if not reason or not reason.strip():
        raise HTTPException(status_code=422, detail="rejectionReason is mandatory and cannot be empty")
        
    claim_obj.status = "Rejected"  # type: ignore
    claim_obj.rejection_reason = reason  # type: ignore
    claim_obj.processed_at = datetime.now()  # type: ignore
    claim_obj.processed_by_id = current_user.id  # type: ignore
    db.add(claim_obj)
    
    audit_log = ClaimAuditLog(
        claim_id=claim_obj.id,
        action=ClaimAction.REJECT,
        processed_by_id=current_user.id,
        rejection_reason=reason
    )
    db.add(audit_log)
    
    await db.commit()
    
    updated_item = await crud_claim.get(db, id=id)
    return {
        "success": True,
        "message": "Claim rejected successfully",
        "data": updated_item
    }

@router.post("/{id}/endorse", response_model=ClaimResponse)
async def endorse_claim(
    id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.PermissionChecker(["SUPERADMINISTRATOR", "NEMSASADMIN", "ADMINSEMSASUSER", "NEMSASUSER", "SEMSASUSER"]))
) -> Any:
    claim_obj = await crud_claim.get(db, id=id)
    if not claim_obj:
        raise HTTPException(status_code=404, detail="Claim not found")
        
    user_type = getattr(current_user, "user_type", None)
    if user_type in ["ADMINSEMSASUSER", "SEMSASUSER", "SEMSASDISPATCH"]:
        if current_user.state_id is None:
            raise HTTPException(status_code=403, detail="State ID is required for state-level users")
        if not claim_obj.incident or claim_obj.incident.state_id != current_user.state_id:
            raise HTTPException(status_code=403, detail="The user doesn't have enough privileges to endorse claims in this state")
            
    claim_obj.status = "Endorsed"  # type: ignore
    claim_obj.processed_at = datetime.now()  # type: ignore
    claim_obj.processed_by_id = current_user.id  # type: ignore
    db.add(claim_obj)
    
    audit_log = ClaimAuditLog(
        claim_id=claim_obj.id,
        action=ClaimAction.ENDORSE,
        processed_by_id=current_user.id
    )
    db.add(audit_log)
    
    await db.commit()
    
    updated_item = await crud_claim.get(db, id=id)
    return {
        "success": True,
        "message": "Claim endorsed successfully",
        "data": updated_item
    }


# ----------------- Legacy Compatibility Models -----------------

class ClaimBindingModel(BaseModel):
    title: Optional[str] = Field(None, alias="title")
    incidentId: int = Field(..., alias="incidentId")
    runSheetId: int = Field(..., alias="runSheetId")
    ambulanceId: Optional[int] = Field(None, alias="ambulanceId")
    hospitalId: Optional[int] = Field(None, alias="hospitalId")
    totalPrice: float = Field(..., alias="totalPrice")
    nhiaOrSHIA: Optional[str] = Field(None, alias="nhiaOrSHIA")
    serviceType: Optional[str] = Field(None, alias="serviceType")
    ambulanceType: Optional[str] = Field(None, alias="ambulanceType")
    distanceCovered: float = Field(..., alias="distanceCovered")
    rejectionReason: Optional[str] = Field(None, alias="rejectionReason")
    image: Optional[str] = Field(None, alias="image")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class CustomRequiredIdModel(BaseModel):
    id: int


class CustomRequiredIdAndBoolModel(BaseModel):
    id: int
    claimStatusType: str = Field(..., alias="claimStatusType")
    rejectionReason: Optional[str] = Field(None, alias="rejectionReason")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    @model_validator(mode="after")
    def validate_rejection(self) -> "CustomRequiredIdAndBoolModel":
        if self.claimStatusType and self.claimStatusType.lower() in ["rejected", "reject"]:
            if not self.rejectionReason or not self.rejectionReason.strip():
                raise ValueError("rejectionReason is mandatory and cannot be empty when rejecting a claim")
        return self



class ClaimReviewBindingModel(BaseModel):
    id: int
    review: Optional[str] = None


class ClaimEtcReviewBindingModel(BaseModel):
    id: int
    etcReview: Optional[str] = Field(None, alias="etcReview")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ClaimUpdateBindingModel(BaseModel):
    id: int
    title: Optional[str] = None
    incidentId: Optional[int] = Field(None, alias="incidentId")
    runSheetId: Optional[int] = Field(None, alias="runSheetId")
    ambulanceId: Optional[int] = Field(None, alias="ambulanceId")
    hospitalId: Optional[int] = Field(None, alias="hospitalId")
    status: Optional[str] = None
    totalPrice: Optional[float] = Field(None, alias="totalPrice")
    nhiaOrSHIA: Optional[str] = Field(None, alias="nhiaOrSHIA")
    serviceType: Optional[str] = Field(None, alias="serviceType")
    ambulanceType: Optional[str] = Field(None, alias="ambulanceType")
    distanceCovered: Optional[float] = Field(None, alias="distanceCovered")
    rejectionReason: Optional[str] = Field(None, alias="rejectionReason")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


# ----------------- Legacy Compatibility Endpoints -----------------

@router.post("/addClaim", response_model=ClaimResponse)
async def add_claim_legacy(
    request: Request,
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Legacy multipart/form-data claim creation endpoint matching .NET API.
    """
    form_data = await request.form()
    
    def to_int(val: Any) -> Optional[int]:
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return int(val)
        val_str = str(val).strip()
        if val_str and val_str.lower() != "null":
            try:
                return int(val_str)
            except ValueError:
                return None
        return None

    def to_float(val: Any) -> float:
        if val is None:
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).strip()
        if val_str and val_str.lower() != "null":
            try:
                return float(val_str)
            except ValueError:
                return 0.0
        return 0.0

    def to_str(val: Any) -> Optional[str]:
        if val is None:
            return None
        from fastapi import UploadFile
        if isinstance(val, UploadFile):
            return None
        val_str = str(val).strip()
        if not val_str or val_str.lower() == "null":
            return None
        return val_str

    # Extract fields with multiple possible key shapes (casing & camelCase/snake_case fallbacks)
    title = to_str(form_data.get("title") or form_data.get("Title"))
    incident_id_str = form_data.get("incidentId") or form_data.get("incident_id") or form_data.get("IncidentId")
    run_sheet_id_str = form_data.get("runSheetId") or form_data.get("run_sheet_id") or form_data.get("RunSheetId")
    ambulance_id_str = form_data.get("ambulanceId") or form_data.get("ambulance_id") or form_data.get("AmbulanceId")
    hospital_id_str = form_data.get("hospitalId") or form_data.get("hospital_id") or form_data.get("HospitalId")
    total_price_str = form_data.get("totalPrice") or form_data.get("total_price") or form_data.get("TotalPrice")
    nhia_val = form_data.get("nhiaOrSHIA") or form_data.get("nhia_or_shia") or form_data.get("NHIAOrSHIA") or form_data.get("nhia")
    service_type = form_data.get("serviceType") or form_data.get("service_type") or form_data.get("ServiceType")
    ambulance_type = form_data.get("ambulanceType") or form_data.get("ambulance_type") or form_data.get("AmbulanceType")
    distance_covered_str = form_data.get("distanceCovered") or form_data.get("distance_covered") or form_data.get("DistanceCovered")
    rejection_reason = form_data.get("rejectionReason") or form_data.get("rejection_reason") or form_data.get("RejectionReason")

    # Type conversions
    incident_id = to_int(incident_id_str)
    run_sheet_id = to_int(run_sheet_id_str)
    ambulance_id = to_int(ambulance_id_str)
    hospital_id = to_int(hospital_id_str)
    total_price = to_float(total_price_str)
    distance_covered = to_float(distance_covered_str)

    # Resolve context from RunSheet and Patient
    patient_id = None
    patient_name = None
    nhia = to_str(nhia_val)
    location = None
    incident_category = None
    incident_date_str = None

    if run_sheet_id:
        run_sheet_stmt = select(RunSheet).where(RunSheet.id == run_sheet_id)
        run_sheet_res = await db.execute(run_sheet_stmt)
        run_sheet_obj = run_sheet_res.scalars().first()
        if run_sheet_obj:
            patient_id = run_sheet_obj.patient_id
            patient_name = str(run_sheet_obj.patient_name) if run_sheet_obj.patient_name is not None else None
            if patient_id:
                patient_stmt = select(Patient).where(Patient.id == patient_id)
                patient_res = await db.execute(patient_stmt)
                patient_obj = patient_res.scalars().first()
                if patient_obj:
                    if not nhia:
                        nhia = str(patient_obj.nhia) if patient_obj.nhia is not None else None
                    if not patient_name:
                        patient_name = f"{patient_obj.first_name or ''} {patient_obj.last_name or ''}".strip()
            location = str(run_sheet_obj.route_to) if run_sheet_obj.route_to is not None else None

    if incident_id:
        incident_stmt = select(Incident).where(Incident.id == incident_id)
        incident_res = await db.execute(incident_stmt)
        incident_obj = incident_res.scalars().first()
        if incident_obj:
            if not location:
                location = str(incident_obj.incident_location) if incident_obj.incident_location is not None else None
            if incident_obj.incident_type:
                incident_category = str(incident_obj.incident_type.name) if incident_obj.incident_type.name is not None else None
            if incident_obj.incident_date:
                incident_date_str = incident_obj.incident_date.isoformat()

    if not title:
        title = f"claims for {patient_name or 'Patient'}, {incident_category or 'Incident'}, incident {incident_id}"

    # Handle image upload if a file was supplied
    image_url = None
    if image and image.filename:
        use_cloudinary = settings.UPLOAD_PROVIDER.lower() == "cloudinary"
        if use_cloudinary and not all([settings.CLOUDINARY_CLOUD_NAME, settings.CLOUDINARY_API_KEY, settings.CLOUDINARY_API_SECRET]):
            use_cloudinary = False
            
        contents = await image.read()
        if use_cloudinary:
            try:
                cloudinary.config(
                    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                    api_key=settings.CLOUDINARY_API_KEY,
                    api_secret=settings.CLOUDINARY_API_SECRET,
                    secure=True
                )
                upload_result = cloudinary.uploader.upload(contents)
                image_url = upload_result.get("secure_url")
            except Exception as e:
                print(f"[addClaim] Cloudinary upload failed: {e}. Falling back to local upload.")
                use_cloudinary = False
                
        if not use_cloudinary:
            import uuid
            import os
            upload_dir = "static/uploads"
            os.makedirs(upload_dir, exist_ok=True)
            safe_filename = f"{uuid.uuid4().hex}_{os.path.basename(image.filename)}"
            file_path = os.path.join(upload_dir, safe_filename)
            with open(file_path, "wb") as f:
                f.write(contents)
            base_url = str(request.base_url)
            if not base_url.endswith("/"):
                base_url += "/"
            image_url = f"{base_url}static/uploads/{safe_filename}"

    # Prepare ClaimCreate pydantic schema
    claim_in = ClaimCreate(
        title=title,
        patient_name=patient_name,
        ambulance_type=to_str(ambulance_type),
        incident_category=incident_category,
        nhia=nhia,
        location=location,
        service_provider=to_str(service_type),
        claim_type="Ambulance",
        total_price=total_price,
        distance_covered=distance_covered,
        incident_date=incident_date_str,
        status="New",
        incident_id=incident_id,
        patient_id=patient_id,
        rejection_reason=to_str(rejection_reason),
        image_url=image_url
    )
    
    item = await crud_claim.create(db, obj_in=claim_in, current_user=current_user)
    return {
        "success": True,
        "message": "Claim successfully created",
        "data": item
    }


@router.post("/addClaimList")
async def add_claim_list(
    claims_in: List[ClaimBindingModel],
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Legacy claim list creation endpoint matching .NET API.
    """
    created_items = []
    for claim_bind in claims_in:
        patient_id = None
        patient_name = None
        nhia = claim_bind.nhiaOrSHIA
        location = None
        incident_category = None
        incident_date_str = None

        if claim_bind.runSheetId:
            run_sheet_stmt = select(RunSheet).where(RunSheet.id == claim_bind.runSheetId)
            run_sheet_res = await db.execute(run_sheet_stmt)
            run_sheet_obj = run_sheet_res.scalars().first()
            if run_sheet_obj:
                patient_id = run_sheet_obj.patient_id
                patient_name = str(run_sheet_obj.patient_name) if run_sheet_obj.patient_name is not None else None
                if patient_id:
                    patient_stmt = select(Patient).where(Patient.id == patient_id)
                    patient_res = await db.execute(patient_stmt)
                    patient_obj = patient_res.scalars().first()
                    if patient_obj:
                        if not nhia:
                            nhia = str(patient_obj.nhia) if patient_obj.nhia is not None else None
                        if not patient_name:
                            patient_name = f"{patient_obj.first_name or ''} {patient_obj.last_name or ''}".strip()
                location = str(run_sheet_obj.route_to) if run_sheet_obj.route_to is not None else None

        if claim_bind.incidentId:
            incident_stmt = select(Incident).where(Incident.id == claim_bind.incidentId)
            incident_res = await db.execute(incident_stmt)
            incident_obj = incident_res.scalars().first()
            if incident_obj:
                if not location:
                    location = str(incident_obj.incident_location) if incident_obj.incident_location is not None else None
                if incident_obj.incident_type:
                    incident_category = str(incident_obj.incident_type.name) if incident_obj.incident_type.name is not None else None
                if incident_obj.incident_date:
                    incident_date_str = incident_obj.incident_date.isoformat()

        title = claim_bind.title
        if not title:
            title = f"claims for {patient_name or 'Patient'}, {incident_category or 'Incident'}, incident {claim_bind.incidentId}"

        claim_in = ClaimCreate(
            title=title,
            patient_name=patient_name,
            ambulance_type=claim_bind.ambulanceType,
            incident_category=incident_category,
            nhia=nhia,
            location=location,
            service_provider=claim_bind.serviceType,
            claim_type="Ambulance",
            total_price=claim_bind.totalPrice,
            distance_covered=claim_bind.distanceCovered,
            incident_date=incident_date_str,
            status="New",
            incident_id=claim_bind.incidentId,
            patient_id=patient_id,
            rejection_reason=claim_bind.rejectionReason,
            image_url=claim_bind.image
        )
        item = await crud_claim.create(db, obj_in=claim_in, current_user=current_user)
        created_items.append(item)

    return {
        "success": True,
        "message": f"{len(created_items)} claim(s) successfully created",
        "data": created_items
    }


@router.delete("/delete")
async def delete_claim_legacy(
    body: CustomRequiredIdModel,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.PermissionChecker(["SUPERADMINISTRATOR", "NEMSASADMIN"]))
) -> Any:
    claim_obj = await crud_claim.get(db, id=body.id)
    if not claim_obj:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    await crud_claim.remove(db, id=body.id)
    return {
        "success": True,
        "message": "Claim successfully deleted"
    }


@router.post("/getSingle", response_model=ClaimResponse)
async def get_single_claim(
    body: CustomRequiredIdModel,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    claim_obj = await crud_claim.get(db, id=body.id)
    if not claim_obj:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {
        "success": True,
        "message": "Claim successfully fetched",
        "data": claim_obj
    }


@router.post("/acceptOrRejectClaim", response_model=ClaimResponse)
@router.post("/acceptOrRejectAmbulanceClaim", response_model=ClaimResponse)
async def accept_or_reject_claim(
    body: CustomRequiredIdAndBoolModel,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.PermissionChecker(["SUPERADMINISTRATOR", "NEMSASADMIN", "ADMINSEMSASUSER", "NEMSASUSER", "SEMSASUSER"]))
) -> Any:
    claim_obj = await crud_claim.get(db, id=body.id)
    if not claim_obj:
        raise HTTPException(status_code=404, detail="Claim not found")

    user_type = getattr(current_user, "user_type", None)
    if user_type in ["ADMINSEMSASUSER", "SEMSASUSER", "SEMSASDISPATCH"]:
        if current_user.state_id is None:
            raise HTTPException(status_code=403, detail="State ID is required for state-level users")
        if not claim_obj.incident or claim_obj.incident.state_id != current_user.state_id:
            raise HTTPException(status_code=403, detail="The user doesn't have enough privileges to modify claims in this state")

    status_str = body.claimStatusType
    action = None
    if status_str.lower() in ["approved", "approve"]:
        if user_type in ["ADMINSEMSASUSER", "SEMSASUSER", "SEMSASDISPATCH"]:
            raise HTTPException(
                status_code=403,
                detail="SEMSAS users cannot directly approve claims. They must endorse them instead."
            )
        setattr(claim_obj, "status", "Approved")
        action = ClaimAction.APPROVE
    elif status_str.lower() in ["rejected", "reject"]:
        setattr(claim_obj, "status", "Rejected")
        setattr(claim_obj, "rejection_reason", body.rejectionReason)
        action = ClaimAction.REJECT
    else:
        setattr(claim_obj, "status", status_str)
        if "endorse" in status_str.lower():
            action = ClaimAction.ENDORSE

    setattr(claim_obj, "processed_at", datetime.now())
    setattr(claim_obj, "processed_by_id", current_user.id)
    db.add(claim_obj)

    if action:
        audit_log = ClaimAuditLog(
            claim_id=claim_obj.id,
            action=action,
            processed_by_id=current_user.id,
            rejection_reason=getattr(claim_obj, "rejection_reason", None)
        )
        db.add(audit_log)

    await db.commit()

    updated_item = await crud_claim.get(db, id=body.id)
    return {
        "success": True,
        "message": f"Claim status updated to {getattr(claim_obj, 'status')}",
        "data": updated_item
    }


@router.put("/addReview")
async def add_review_claim(
    body: ClaimReviewBindingModel,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    claim_obj = await crud_claim.get(db, id=body.id)
    if not claim_obj:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    setattr(claim_obj, "review", body.review)
    db.add(claim_obj)
    await db.commit()
    
    updated_item = await crud_claim.get(db, id=body.id)
    return {
        "success": True,
        "message": "Claim review updated successfully",
        "data": updated_item
    }


@router.put("/addEtcReview")
async def add_etc_review_claim(
    body: ClaimEtcReviewBindingModel,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    claim_obj = await crud_claim.get(db, id=body.id)
    if not claim_obj:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    setattr(claim_obj, "etc_review", body.etcReview)
    db.add(claim_obj)
    await db.commit()
    
    updated_item = await crud_claim.get(db, id=body.id)
    return {
        "success": True,
        "message": "Claim ETC review updated successfully",
        "data": updated_item
    }


@router.post("/update", response_model=ClaimResponse)
async def update_claim_legacy(
    body: ClaimUpdateBindingModel,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    claim_obj = await crud_claim.get(db, id=body.id)
    if not claim_obj:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    if body.title is not None:
        setattr(claim_obj, "title", body.title)
    if body.incidentId is not None:
        setattr(claim_obj, "incident_id", body.incidentId)
    if body.runSheetId is not None:
        run_sheet_stmt = select(RunSheet).where(RunSheet.id == body.runSheetId)
        run_sheet_res = await db.execute(run_sheet_stmt)
        run_sheet_obj = run_sheet_res.scalars().first()
        if run_sheet_obj:
            setattr(claim_obj, "patient_id", run_sheet_obj.patient_id)
            if run_sheet_obj.patient_name:
                setattr(claim_obj, "patient_name", str(run_sheet_obj.patient_name))
    if body.status is not None:
        setattr(claim_obj, "status", body.status)
        if body.status.lower() in ["rejected", "reject"]:
            reason = body.rejectionReason or getattr(claim_obj, "rejection_reason", None)
            if not reason or not str(reason).strip():
                raise HTTPException(status_code=422, detail="rejectionReason is mandatory and cannot be empty when status is Rejected")
    if body.totalPrice is not None:
        setattr(claim_obj, "total_price", body.totalPrice)
    if body.nhiaOrSHIA is not None:
        setattr(claim_obj, "nhia", body.nhiaOrSHIA)
    if body.serviceType is not None:
        setattr(claim_obj, "service_provider", body.serviceType)
    if body.ambulanceType is not None:
        setattr(claim_obj, "ambulance_type", body.ambulanceType)
    if body.distanceCovered is not None:
        setattr(claim_obj, "distance_covered", body.distanceCovered)
    if body.rejectionReason is not None:
        setattr(claim_obj, "rejection_reason", body.rejectionReason)
        
    db.add(claim_obj)
    await db.commit()
    
    updated_item = await crud_claim.get(db, id=body.id)
    return {
        "success": True,
        "message": "Claim successfully updated",
        "data": updated_item
    }
