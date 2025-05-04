from fastapi import APIRouter, Depends, HTTPException
from fastapi import UploadFile, File

from core.dependecies import get_media_service
from services.media.MediaService import MediaService
from models.api.media.responses import UploadFileResponse, GetPresignedUrlResponse

router = APIRouter()

@router.post("/upload", response_model=UploadFileResponse)
async def upload_file(
    file: UploadFile = File(...),
    media_service: MediaService = Depends(get_media_service)
):
    try:
        return await media_service.upload_file(await file.read(), file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/presigned-url", response_model=GetPresignedUrlResponse)
async def get_presigned_url(
    key: str,
    expiration: int,
    media_service: MediaService = Depends(get_media_service)
):
    try:
        return media_service.generate_presigned_url(key, expiration)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/files/{key}")
async def delete_file(
    key: str,
    media_service: MediaService = Depends(get_media_service)
):
    try:
        await media_service.delete_file(key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
