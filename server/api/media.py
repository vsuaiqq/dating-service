from fastapi import APIRouter, Depends, HTTPException
from fastapi import UploadFile, File, Form

from core.dependecies import get_media_service, get_user_id_from_headers
from core.logger import logger
from services.media.MediaService import MediaService
from models.api.media.requests import MediaType
from models.api.media.responses import GetPresignedUrlsResponse

router = APIRouter()

@router.post("/upload")
async def upload_file(
    user_id: int = Depends(get_user_id_from_headers),
    file: UploadFile = File(...),
    type: MediaType = Form(...),
    media_service: MediaService = Depends(get_media_service)
):
    try:
        logger.info(f"Starting file upload: {file.filename}")
        await media_service.upload_file(user_id, await file.read(), file.filename, type)
        logger.info(f"File uploaded successfully: {file.filename}")
    except Exception as e:
        logger.error(
            f"File upload failed: {file.filename}. Error: {str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/presigned-urls", response_model=GetPresignedUrlsResponse)
async def get_presigned_urls(
    user_id: int = Depends(get_user_id_from_headers),
    media_service: MediaService = Depends(get_media_service)
):
    try:
        logger.info(f"Generating presigned URLs for user: {user_id}")
        result = await media_service.generate_presigned_urls(user_id)
        logger.info(f"Presigned URLs generated for user: {user_id}")
        return result
    except Exception as e:
        logger.error(
            f"Failed to generate presigned URL for user: {user_id}. Error: {str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/files")
async def delete_files(
    user_id: int = Depends(get_user_id_from_headers),
    media_service: MediaService = Depends(get_media_service)
):
    try:
        logger.info(f"Deleting files for user: {user_id}")
        await media_service.delete_files(user_id)
        logger.info(f"Files deleted successfully for user: {user_id}")
    except Exception as e:
        logger.error(
            f"Failed to delete files for user: {user_id}. Error: {str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))
