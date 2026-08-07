import logging
import os
import uuid
from typing import Optional
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_s3_client():
    """Constructs and returns a boto3 S3 client configured for AWS or custom S3 providers (e.g. Hetzner)."""
    endpoint = settings.S3_ENDPOINT_URL
    if endpoint and not endpoint.startswith("http://") and not endpoint.startswith("https://"):
        endpoint = f"https://{endpoint}"

    return boto3.client(
        "s3",
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        endpoint_url=endpoint,
        region_name=settings.S3_REGION or "eu-central"
    )

def upload_file_to_s3(file_bytes: bytes, filename: Optional[str] = "upload.jpg", content_type: str = "application/octet-stream") -> Optional[str]:
    """
    Uploads a file to S3 / Hetzner Object Storage and returns the public URL.
    Returns None if S3 is misconfigured or if upload fails.
    """
    access_key = settings.S3_ACCESS_KEY
    secret_key = settings.S3_SECRET_KEY
    endpoint = settings.S3_ENDPOINT_URL
    bucket_name = settings.S3_BUCKET_NAME

    if not access_key or not secret_key or not endpoint or not bucket_name:
        logger.warning("[S3 Upload] S3 credentials or bucket name missing in configuration.")
        return None

    ext = os.path.splitext(filename)[1] if filename else ".jpg"
    safe_filename = f"{uuid.uuid4().hex}{ext}"

    try:
        s3_client = get_s3_client()
        
        try:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=safe_filename,
                Body=file_bytes,
                ContentType=content_type,
                ACL="public-read"
            )
        except Exception as acl_error:
            logger.warning(f"[S3 Upload] PutObject with public-read ACL failed ({acl_error}), retrying without ACL...")
            s3_client.put_object(
                Bucket=bucket_name,
                Key=safe_filename,
                Body=file_bytes,
                ContentType=content_type
            )

        clean_endpoint = endpoint.replace("https://", "").replace("http://", "").rstrip("/")
        url = f"https://{bucket_name}.{clean_endpoint}/{safe_filename}"
        logger.info(f"[S3 Upload] File successfully uploaded to S3: {url}")
        return url
    except (BotoCoreError, ClientError, Exception) as e:
        logger.error(f"[S3 Upload] Failed to upload file to S3: {e}")
        return None
