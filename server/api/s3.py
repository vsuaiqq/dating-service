from fastapi import APIRouter, Depends, HTTPException
from fastapi import UploadFile, File

from core.dependecies import get_s3_service
from services.s3.S3Service import S3Service
from models.s3.responses import UploadFileResponse, GetPresignedUrlResponse

router = APIRouter()

@router.post("/upload", response_model=UploadFileResponse)
async def upload_file_to_s3(
    file: UploadFile = File(...),
    s3_service: S3Service = Depends(get_s3_service)
):
    try:
        return await s3_service.upload_file(await file.read(), file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/presigned-url", response_model=GetPresignedUrlResponse)
async def get_presigned_url(
    key: str,
    expiration: int,
    s3_service: S3Service = Depends(get_s3_service)
):
    try:
        return s3_service.generate_presigned_url(key, expiration)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/files/{key}")
async def delete_file_from_s3(
    key: str,
    s3_service: S3Service = Depends(get_s3_service)
):
    try:
        await s3_service.delete_file(key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
