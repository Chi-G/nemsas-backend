from typing import Any, Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, extract
from app.api import deps
from app.models.user import User
from app.models.patient import Patient
from app.models.incident import Incident
from app.models.state import State
from app.models.hospital import Hospital
from app.models.ambulance import Ambulance
from app.models.medical_intervention import MedicalIntervention 
from app.models.etc_intervention import EtcIntervention
from app.models.drug import Drug
from app.models.service import Service
from app.models.fee_category import FeeCategory
from app.schemas.etc_intervention import EtcInterventionBase
from app.schemas.patient import PatientUpdate
from pydantic import BaseModel
from datetime import date, datetime 

router = APIRouter()

class ETCPatientResponseDto(BaseModel):
    id: int
    firstName: Optional[str] = None
    middleName: Optional[str] = None
    lastName: Optional[str] = None
    doB: Optional[date] = None
    sex: Optional[int] = None
    phoneNumber: Optional[str] = None
    address: Optional[str] = None
    nhia: Optional[str] = None
    state: Optional[str] = None

class ETCPatientPaginatedResponse(BaseModel):
    success: bool = True
    message: str = "ETC patients fetched successfully"
    data: dict
    totalCount: int
    refreshToken: Optional[str] = None
    refreshTokenExpiryTime: str = "0001-01-01T00:00:00"

@router.get("/etc", response_model=ETCPatientPaginatedResponse)
async def get_etc_patients(
    db: AsyncSession = Depends(deps.get_db),
    page: int = 1,
    pageSize: int = 20,
    year: Optional[int] = None,
    month: Optional[int] = None,
    gender: Optional[int] = None,
    search: Optional[str] = None,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get all patients assigned to the ETC of the current user.
    Only accessible by EMERGENCYTREATMENTUSER.
    """
    user_type = getattr(current_user, "user_type", None)
    if user_type != "EMERGENCYTREATMENTUSER":
        raise HTTPException(status_code=403, detail="Only EMERGENCYTREATMENTUSER can access this endpoint")
        
    etc_id = getattr(current_user, "etc_id", None) or getattr(current_user, "emergency_treatment_center_id", None)
    if etc_id is None:
        raise HTTPException(status_code=403, detail="ETC ID is required for ETC users")

    skip = (page - 1) * pageSize
    
    # Base query for patient and state name (joined via Incident)
    stmt = select(Patient, State.name.label("state_name")).outerjoin(
        Incident, Patient.incident_id == Incident.id
    ).outerjoin(
        State, Incident.state_id == State.id
    ).where(Patient.etc_id == etc_id)
    
    # Count query
    count_stmt = select(func.count(Patient.id)).outerjoin(
        Incident, Patient.incident_id == Incident.id
    ).where(Patient.etc_id == etc_id)
    
    # Gender filter
    if gender is not None:
        stmt = stmt.where(Patient.sex == gender)
        count_stmt = count_stmt.where(Patient.sex == gender)
        
    # Search filter (firstName, middleName, lastName)
    if search:
        search_filter = or_(
            Patient.first_name.ilike(f"%{search}%"),
            Patient.last_name.ilike(f"%{search}%"),
            Patient.middle_name.ilike(f"%{search}%")
        )
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)
        
    # Year filter on incident
    if year is not None:
        stmt = stmt.where(extract('year', Incident.date_added) == year)
        count_stmt = count_stmt.where(extract('year', Incident.date_added) == year)
        
    # Month filter on incident
    if month is not None:
        stmt = stmt.where(extract('month', Incident.date_added) == month)
        count_stmt = count_stmt.where(extract('month', Incident.date_added) == month)
        
    # Apply pagination and ordering
    stmt = stmt.order_by(Patient.created_at.desc()).offset(skip).limit(pageSize)    
    # Execute queries
    total = (await db.execute(count_stmt)).scalar() or 0
    results = await db.execute(stmt)
    
    items = []
    for patient, state_name in results.all():
        items.append(ETCPatientResponseDto(
            id=patient.id,
            firstName=patient.first_name,
            middleName=patient.middle_name,
            lastName=patient.last_name,
            doB=patient.do_b,
            sex=patient.sex,
            phoneNumber=patient.phone_number,
            address=patient.address,
            nhia=patient.nhia,
            state=state_name
        ).model_dump())
        
    return {
        "success": True,
        "message": "ETC patients fetched successfully",
        "data": {"items": items},
        "totalCount": total
    }

@router.get("/{patient_id}")
async def get_patient_details(
    patient_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get detailed information about a patient, including their assigned ETC, 
    Ambulance, and all related interventions (ETC and Medical).
    """
    # 1. Fetch Patient
    stmt_patient = select(Patient).where(Patient.id == patient_id)
    patient = (await db.execute(stmt_patient)).scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    # 2. Fetch Hospital (ETC)
    hospital = None
    if patient.etc_id:
        stmt_hosp = select(Hospital).where(Hospital.id == patient.etc_id)
        hospital = (await db.execute(stmt_hosp)).scalar_one_or_none()
        
    # 3. Fetch Ambulance
    ambulance = None
    if patient.ambulance_id:
        stmt_amb = select(Ambulance).where(Ambulance.id == patient.ambulance_id)
        ambulance = (await db.execute(stmt_amb)).scalar_one_or_none()
        
    # 4. Fetch Medical Interventions
    stmt_med = select(MedicalIntervention).where(MedicalIntervention.patient_id == patient_id)
    med_invs = (await db.execute(stmt_med)).scalars().all()
    
    # Helper to convert SQLAlchemy models to dictionaries
    def obj_to_dict(obj):
        if not obj:
            return None
        res = {}
        for c in obj.__table__.columns:
            val = getattr(obj, c.name)
            # Serialize datetimes to ISO format for JSON responses
            if isinstance(val, (datetime, date)):
                res[c.name] = val.isoformat()
            else:
                res[c.name] = val
        return res

    # 5. Fetch ETC Interventions (via Incident) and their associated drugs (services)
    etc_invs = []
    if patient.incident_id:
        # The `drug_id` field actually maps to the `services` table in the database
        stmt_etc = select(EtcIntervention, Service, FeeCategory.is_medicine).outerjoin(
            Service, EtcIntervention.drug_id == Service.id
        ).outerjoin(
            FeeCategory, Service.fee_category_id == FeeCategory.id
        ).where(EtcIntervention.patient_id == patient_id)
        
        results = await db.execute(stmt_etc)
        for e_inv, service, is_medicine in results.all():
            e_dict = obj_to_dict(e_inv)
            drug_dict = obj_to_dict(service)
            if drug_dict is not None:
                drug_dict["isMedicine"] = is_medicine if is_medicine is not None else False
                e_dict["code"] = drug_dict.get("code")
            e_dict["drug"] = drug_dict
            etc_invs.append(e_dict)

    patient_dict = obj_to_dict(patient)
    if patient.incident_id:
        stmt_inc = select(Incident).where(Incident.id == patient.incident_id)
        incident = (await db.execute(stmt_inc)).scalar_one_or_none()
        if incident:
            patient_dict["triageCategory"] = incident.triage_category

    # 6. Fetch Claim and Claim Images (if any)
    from app.models.claim import Claim, ClaimImage
    stmt_claim = select(Claim).where(Claim.patient_id == patient_id, Claim.etc_claim_status != "Not Applicable")
    claim = (await db.execute(stmt_claim)).scalar_one_or_none()
    claim_dict = None
    if claim:
        claim_dict = obj_to_dict(claim)
        stmt_images = select(ClaimImage).where(ClaimImage.claim_id == claim.id)
        images = (await db.execute(stmt_images)).scalars().all()
        claim_dict["images"] = [obj_to_dict(img) for img in images]

    # 7. Fetch Transfer Form creation time
    transfer_form_created_at = None
    if patient.incident_id:
        from app.models.transfer_form import TransferForm
        stmt_tf = select(TransferForm.created_at).where(TransferForm.incident_id == patient.incident_id).order_by(TransferForm.created_at.desc())
        tf_time = (await db.execute(stmt_tf)).scalar_one_or_none()
        if tf_time:
            # Need to format or return string?
            transfer_form_created_at = tf_time.isoformat() if hasattr(tf_time, 'isoformat') else str(tf_time)

    return {
        "success": True,
        "message": "Patient details fetched successfully",
        "data": {
            "patient": patient_dict,
            "hospital": obj_to_dict(hospital),
            "ambulance": obj_to_dict(ambulance),
            "medicalInterventions": [obj_to_dict(m) for m in med_invs],
            "interventions": etc_invs,
            "claim": claim_dict,
            "transferFormCreatedAt": transfer_form_created_at
        }
    }

@router.post("/{patient_id}/addIntervention")
async def add_etc_interventions(
    patient_id: int,
    request: Request,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Add multiple ETC interventions (services/drugs) to a patient via FormData.
    Also creates an ETC-specific claim tied to this patient and saves images.
    """
    user_type = getattr(current_user, "user_type", None)
    if user_type != "EMERGENCYTREATMENTUSER":
        raise HTTPException(status_code=403, detail="Only EMERGENCYTREATMENTUSER can access this endpoint")
        
    etc_id = getattr(current_user, "etc_id", None) or getattr(current_user, "emergency_treatment_center_id", None)
    if etc_id is None:
        raise HTTPException(status_code=403, detail="ETC ID is required for ETC users")

    # Fetch patient to verify access
    stmt = select(Patient).where(Patient.id == patient_id)
    patient = (await db.execute(stmt)).scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    if patient.etc_id != etc_id:
        raise HTTPException(status_code=403, detail="Patient is not assigned to your ETC")
        
    if not patient.incident_id:
        raise HTTPException(status_code=400, detail="Patient does not have an associated incident")
        
    form_data = await request.form()
    interventions_json = form_data.get("interventions")
    if not interventions_json:
        raise HTTPException(status_code=400, detail="Missing interventions in form data")
        
    import json
    try:
        interventions_list = json.loads(str(interventions_json))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid interventions JSON")

    images = form_data.getlist("images")
    if not images:
        raise HTTPException(status_code=400, detail="At least one image is required")

    # Get current max ID for etc_interventions
    max_id_stmt = select(func.max(EtcIntervention.id))
    max_id = (await db.execute(max_id_stmt)).scalar() or 0
    next_id = max_id + 1
        
    total_price = 0.0

    # Create interventions
    for intervention_data in interventions_list:
        # Build dict safely
        intervention_dict = {
            "drug_id": intervention_data.get("drug_id") or intervention_data.get("drugId"),
            "medical_intervention": intervention_data.get("medical_intervention") or intervention_data.get("medicalIntervention"),
            "price": float(intervention_data.get("price", 0)),
            "dose": intervention_data.get("dose", 0),
            "diagnosis": intervention_data.get("diagnosis"),
            "quantity": int(intervention_data.get("quantity", 1)),
            "incident_id": patient.incident_id,
            "patient_id": patient_id,
            "emergency_treatment_center_id": etc_id,
            "id": next_id
        }
        total_price += intervention_dict["price"] * intervention_dict["quantity"]
        
        # Default date if not provided
        from datetime import timezone
        intervention_dict["date_added"] = datetime.now(timezone.utc)
            
        db_obj = EtcIntervention(**intervention_dict)
        db.add(db_obj)
        next_id += 1

    # Create the new ETC-specific Claim
    from app.models.claim import Claim, ClaimImage
    from app.models.incident_type import IncidentType
    
    # fetch hospital details for location/provider name if possible
    stmt_hospital = select(Hospital).where(Hospital.id == etc_id)
    hospital = (await db.execute(stmt_hospital)).scalar_one_or_none()
    provider_name = hospital.name if hospital else "ETC Provider"
    
    patient_name = f"{patient.first_name or ''} {patient.last_name or ''}".strip()
    
    # Fetch incident and category
    stmt_inc = select(Incident, IncidentType.name).outerjoin(
        IncidentType, Incident.incident_category_id == IncidentType.id
    ).where(Incident.id == patient.incident_id)
    inc_res = (await db.execute(stmt_inc)).first()
    
    inc_category = "ETC Treatment"
    inc_date = None
    if inc_res:
        inc_obj, inc_type_name = inc_res
        if inc_type_name:
            inc_category = inc_type_name
        if inc_obj.incident_date:
            try:
                inc_date = inc_obj.incident_date.isoformat()
            except AttributeError:
                inc_date = str(inc_obj.incident_date)
    
    new_claim = Claim(
        incident_id=patient.incident_id,
        patient_id=patient_id,
        user_id=current_user.id,
        title=f"ETC Claim for {patient_name}",
        patient_name=patient_name,
        incident_category=inc_category,
        incident_date=inc_date,
        nhia=patient.nhia,
        service_provider=provider_name,
        total_price=total_price,
        amount=total_price,
        etc_claim_status="Pending",
        ambulance_claim_status="Not Applicable"
    )
    db.add(new_claim)
    await db.commit()
    await db.refresh(new_claim)

    # Process Images
    from app.core.config import settings 
    import cloudinary
    import cloudinary.uploader
    import uuid
    import os
    
    use_cloudinary = settings.UPLOAD_PROVIDER.lower() == "cloudinary"
    if use_cloudinary:
        if not all([settings.CLOUDINARY_CLOUD_NAME, settings.CLOUDINARY_API_KEY, settings.CLOUDINARY_API_SECRET]):
            use_cloudinary = False

    if use_cloudinary:
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )

    for file_obj in images:
        contents = await file_obj.read()
        url = None
        
        if use_cloudinary:
            try:
                upload_result = cloudinary.uploader.upload(contents)
                url = upload_result.get("secure_url")
            except Exception:
                use_cloudinary = False
                
        if not use_cloudinary:
            upload_dir = "static/uploads"
            os.makedirs(upload_dir, exist_ok=True)
            safe_filename = f"{uuid.uuid4().hex}_{os.path.basename(file_obj.filename or 'upload.jpg')}"
            file_path = os.path.join(upload_dir, safe_filename)
            with open(file_path, "wb") as f:
                f.write(contents)
            base_url = str(request.base_url)
            if not base_url.endswith("/"):
                base_url += "/"
            url = f"{base_url}static/uploads/{safe_filename}"
            
        if url:
            # Find next image ID
            max_img_stmt = select(func.max(ClaimImage.id))
            max_img_id = await db.scalar(max_img_stmt) or 0
            new_image_id = max_img_id + 1
            
            db_image = ClaimImage(
                id=new_image_id,
                claim_id=new_claim.id,
                claim_title=new_claim.title,
                incident_id=patient.incident_id,
                image_url=url,
                is_etc=True
            )
            db.add(db_image)
            await db.commit()
    
    return {
        "success": True,
        "message": f"Successfully added {len(interventions_list)} ETC intervention(s) and created a new claim."
    }

@router.put("/{patient_id}")
async def update_patient_details(
    patient_id: int,
    patient_in: PatientUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Update patient details.
    Only the ETC assigned to the patient can perform this action.
    """
    user_type = getattr(current_user, "user_type", None)
    if user_type != "EMERGENCYTREATMENTUSER":
        raise HTTPException(status_code=403, detail="Only EMERGENCYTREATMENTUSER can access this endpoint")
        
    etc_id = getattr(current_user, "etc_id", None) or getattr(current_user, "emergency_treatment_center_id", None)
    if etc_id is None:
        raise HTTPException(status_code=403, detail="ETC ID is required for ETC users")

    # Fetch patient to verify access
    stmt = select(Patient).where(Patient.id == patient_id)
    patient = (await db.execute(stmt)).scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    if patient.etc_id != etc_id:
        raise HTTPException(status_code=403, detail="Patient is not assigned to your ETC")
        
    # Update patient fields
    update_data = patient_in.model_dump(exclude_unset=True)
    
    # Ensure they can't maliciously reassign the patient to another ETC or Incident
    if "etc_id" in update_data and update_data["etc_id"] != patient.etc_id:
        raise HTTPException(status_code=400, detail="Cannot change assigned ETC")
        
    for field, value in update_data.items():
        setattr(patient, field, value)
        
    await db.commit()
    await db.refresh(patient)
    
    def obj_to_dict(obj):
        if not obj:
            return None
        res = {}
        for c in obj.__table__.columns:
            val = getattr(obj, c.name)
            if isinstance(val, (datetime, date)):
                res[c.name] = val.isoformat()
            else:
                res[c.name] = val
        return res
        
    return {
        "success": True,
        "message": "Patient details updated successfully",
        "data": obj_to_dict(patient)
    }
