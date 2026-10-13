from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import boto3
from botocore.config import Config
import uuid
import os

from app.modules.auth.dependencies import get_db, get_current_user, get_current_active_user
from app.core.config import settings
from app.core.exceptions import ExternalServiceError


router = APIRouter(prefix="/media", tags=["Media"])


def get_r2_client():
    return boto3.client(
        's3',
        endpoint_url=f'https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        config=Config(signature_version='s3v4'),
        region_name='auto',
    )


@router.post("/upload", response_model=dict)
async def upload_media(
    file: UploadFile = File(...),
    path: str = "uploads",
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Validate file type
    allowed_types = {
        "image/jpeg", "image/png", "image/webp", "image/gif",
        "video/mp4", "video/webm", "video/quicktime",
        "application/pdf", "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File type not allowed")

    # Validate file size (max 50MB)
    max_size = 50 * 1024 * 1024
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")

    # Generate key
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    key = f"{path}/{current_user.lodge_id}/{current_user.id}/{uuid.uuid4()}{ext}"

    try:
        client = get_r2_client()
        client.put_object(
            Bucket=settings.R2_BUCKET,
            Key=key,
            Body=file_content,
            ContentType=file.content_type,
            ACL='public-read',
        )
    except Exception as e:
        raise ExternalServiceError(f"Upload failed: {str(e)}")

    public_url = f"{settings.R2_PUBLIC_URL}/{key}"

    return {
        "url": public_url,
        "key": key,
        "content_type": file.content_type,
        "size": len(file_content),
    }


@router.delete("/{key:path}")
async def delete_media(
    key: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        client = get_r2_client()
        client.delete_object(Bucket=settings.R2_BUCKET, Key=key)
    except Exception as e:
        raise ExternalServiceError(f"Delete failed: {str(e)}")

    return {"message": "Media deleted"}


@router.post("/signed-url")
async def get_signed_url(
    key: str,
    expires_in: int = 3600,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    client = get_r2_client()
    try:
        url = client.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.R2_BUCKET, 'Key': key},
            ExpiresIn=expires_in,
        )
    except Exception as e:
        raise ExternalServiceError(f"Failed to generate signed URL: {str(e)}")

    return {"url": url, "expires_in": expires_in}