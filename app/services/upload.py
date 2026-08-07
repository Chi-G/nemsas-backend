import logging
import os
import uuid
from typing import Optional
from fastapi import Request
from app.core.config import settings
from app.services.s3 import upload_file_to_s3

logger = logging.getLogger(__name__)

async def upload_file_helper(
    file_bytes: bytes,
    filename: Optional[str] = "upload.jpg",
    content_type: str = "application/octet-stream",
    request: Optional[Request] = None
) -> str:
    """
    Centralized file upload handler supporting S3 (Hetzner), Cloudinary, and Local Disk storage fallback.
    """
    provider = settings.UPLOAD_PROVIDER.lower()

    # 1. Try S3 / Hetzner if configured
    if provider in ["s3", "hetzner"]:
        s3_url = upload_file_to_s3(file_bytes=file_bytes, filename=filename, content_type=content_type)
        if s3_url:
            return s3_url
        logger.warning("[Upload] S3 upload failed or misconfigured. Falling back to local storage.")

    # 2. Try Cloudinary if configured
    if provider == "cloudinary":
        if all([settings.CLOUDINARY_CLOUD_NAME, settings.CLOUDINARY_API_KEY, settings.CLOUDINARY_API_SECRET]):
            try:
                import cloudinary
                import cloudinary.uploader
                cloudinary.config(
                    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                    api_key=settings.CLOUDINARY_API_KEY,
                    api_secret=settings.CLOUDINARY_API_SECRET,
                    secure=True
                )
                upload_result = cloudinary.uploader.upload(file_bytes)
                url = upload_result.get("secure_url")
                if url:
                    return url
            except Exception as e:
                logger.warning(f"[Upload] Cloudinary upload failed: {e}. Falling back to local storage.")

    # 3. Fallback to Local Disk Storage
    upload_dir = "static/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    clean_filename = os.path.basename(filename or "upload.jpg")
    safe_filename = f"{uuid.uuid4().hex}_{clean_filename}"
    file_path = os.path.join(upload_dir, safe_filename)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    if request:
        base_url = str(request.base_url)
        if not base_url.endswith("/"):
            base_url += "/"
        return f"{base_url}static/uploads/{safe_filename}"

    return f"/static/uploads/{safe_filename}"
