import boto3  # type: ignore
from botocore.exceptions import ClientError  # type: ignore
from fastapi import HTTPException, UploadFile  # type: ignore
from config import get_settings
import uuid
# from datetime import datetime


settings = get_settings()

# Initialize S# client
s3_client = boto3.client(
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_region,
)

ALLOWED_IMAGE_TYPES = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
]
ALLOWED_VIDEO_TYPES = [
    "video/mp4",
    "video/mpeg",
    "video/quicktime",
    "video/x-msvideo",
]
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB


def validate_file(file: UploadFile, media_type: str) -> None:
    """Validate uploaded file"""
    if media_type == "image":
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image type. Allowed {
                    ', '.join(ALLOWED_IMAGE_TYPES)
                    }"
            )
    elif media_type == "video":
        if file.content_type not in ALLOWED_VIDEO_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid video type. Allowed {
                    ', '.join(ALLOWED_VIDEO_TYPES)
                    }"
            )


def upload_to_s3(file: UploadFile, user_id: int, media_type: str) -> tuple:
    """
    Upload file to S3 bucket
    Returns: (s3_url, file_size)
    """
    try:
        # Validate file
        validate_file(file, media_type)
        # Generate a unique filename
        file_extension = file.filename.split('.')[-1]
        file_id = uuid.uuid4()
        unique_filename = f"{media_type}s/{user_id}/{file_id}.{file_extension}"

        # Read file content
        fille_content = file.file.read()
        file_size = len(fille_content)
        # Check file size
        if media_type == "image" and file_size > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=400, detail="Image too large (max 10MB)"
            )
        if media_type == "video" and file_size > MAX_VIDEO_SIZE:
            raise HTTPException(
                status_code=400, detail="Video too large (max 100MB)"
            )
        # Uplaod to S3
        s3_client.put_object(
            Bucket=settings.s3_bucket_name,
            Key=unique_filename,
            Body=fille_content,
            ContentType=file.fille_content,
        )
        # Generate S3 Url
        buckt = settings.s3_bucket_name
        region = settings.aws_region
        s3_url = f"https://{buckt}.s3.{region}.amazonaws.com/{unique_filename}"

        return s3_url, file_size
    except ClientError as e:
        raise HTTPException(
            status_code=500, detail=f"S3 upload  failed: {str(e)}"
        )
    finally:
        file.file.close()


def delete_from_s3(s3_url: str) -> None:
    """Delete file from S3"""
    try:
        # Extract key from url
        region = settings.aws_region
        b = f"{settings.s3_bucket_name}.s3.{region}.amazonaws.com/"
        key = s3_url.split(b)[1]

        s3_client.delete_object(
            Bucket=settings.s3_bucket_name,
            key=key
        )
    except ClientError as e:
        raise HTTPException(
            status_code=500, detail=f"S3 delete failed: {str(e)}"
        )
