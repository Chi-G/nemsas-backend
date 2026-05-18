from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.models.user import User
from app.schemas.claim import ClaimPaginatedResponse, ClaimResponse, ClaimCreate
from app.crud.claim import claim as crud_claim
from app.crud.claim_setting import claim_setting as crud_setting
from app.schemas.claim_setting import ClaimSetting
from typing import List
from fastapi import UploadFile, File
import cloudinary
import cloudinary.uploader
from app.core.config import settings

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
    month: Optional[int] = None
) -> Any:
    """
    Get claims for ambulances or etc.
    Supports standard filtering parameters provided by the user workflow.
    """
    items, total = await crud_claim.get_multi_with_count(
        db,
        skip=skip,
        limit=limit,
        status=status,
        query_review=query,
        year=year,
        month=month
    )
    return {
        "success": True,
        "message": "Claim(s) successfully fetched",
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
