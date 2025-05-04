from fastapi import APIRouter, Depends, HTTPException
from fastapi import UploadFile, File

from core.dependecies import get_media_service
from core.logger import logger
from services.media.MediaService import MediaService
from models.api.media.responses import UploadFileResponse, GetPresignedUrlResponse

router = APIRouter()

@router.post("/upload", response_model=UploadFileResponse)
async def upload_file(
    file: UploadFile = File(...),
    media_service: MediaService = Depends(get_media_service)
):
    try:
        logger.info(f"Starting file upload: {file.filename}")
        result = await media_service.upload_file(await file.read(), file.filename)
        logger.info(f"File uploaded successfully: {file.filename}")
        return result
    except Exception as e:
        logger.error(
            f"File upload failed: {file.filename}. Error: {str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/presigned-url", response_model=GetPresignedUrlResponse)
async def get_presigned_url(
    key: str,
    expiration: int,
    media_service: MediaService = Depends(get_media_service)
):
    try:
        logger.info(f"Generating presigned URL for key: {key}")
        result = media_service.generate_presigned_url(key, expiration)
        logger.info(f"Presigned URL generated for key: {key}")
        return result
    except Exception as e:
        logger.error(
            f"Failed to generate presigned URL for key: {key}. Error: {str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/files/{key}")
async def delete_file(
    key: str,
    media_service: MediaService = Depends(get_media_service)
):
    try:
        logger.info(f"Deleting file with key: {key}")
        await media_service.delete_file(key)
        logger.info(f"File deleted successfully: {key}")
        return {"status": "success", "message": f"File {key} deleted"}
    except Exception as e:
        logger.error(
            f"Failed to delete file: {key}. Error: {str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))