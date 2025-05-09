from fastapi import APIRouter, Depends
from fastapi import UploadFile, File, Form
from dependency_injector.wiring import inject, Provide

from api.v1.dependecies.headers import get_user_id_from_headers
from api.v1.schemas.media import MediaType, GetPresignedUrlsResponse
from domain.media.services.media_service import MediaService
from di.container import Container
from core.logger import logger

router = APIRouter()

@router.post("/upload")
@inject
async def upload_file(
    user_id: int = Depends(get_user_id_from_headers),
    file: UploadFile = File(...),
    type: MediaType = Form(...),
    media_service: MediaService = Depends(Provide[Container.services.provided.media])
):
    logger.info(f"Starting file upload: {file.filename}")
    await media_service.upload_file(user_id, await file.read(), file.filename, type)
    logger.info(f"File uploaded successfully: {file.filename}")

@router.get("/presigned-urls", response_model=GetPresignedUrlsResponse)
@inject
async def get_presigned_urls(
    user_id: int = Depends(get_user_id_from_headers),
    media_service: MediaService = Depends(Provide[Container.services.provided.media])
):
    logger.info(f"Generating presigned URLs for user: {user_id}")
    result = await media_service.generate_presigned_urls(user_id)
    logger.info(f"Presigned URLs generated for user: {user_id}")
    return result

@router.delete("/files")
@inject
async def delete_files(
    user_id: int = Depends(get_user_id_from_headers),
    media_service: MediaService = Depends(Provide[Container.services.provided.media])
):
    logger.info(f"Deleting files for user: {user_id}")
    await media_service.delete_files(user_id)
    logger.info(f"Files deleted successfully for user: {user_id}")
