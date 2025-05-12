from fastapi import APIRouter, Request, Depends, UploadFile, File, Form, status
from dependency_injector.wiring import inject, Provide
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.v1.deps.headers import get_user_id_from_headers
from api.v1.schemas.media import MediaType, GetPresignedUrlsResponse
from domain.media.services.media_service import MediaService
from di.container import Container
from core.logger import logger

router = APIRouter()
limiter = Limiter(key_func=get_remote_address, storage_uri=Container.config().redis_url_limiter)


@router.post(
    "/upload",
    tags=["Media"],
    summary="Upload media file",
    description="Upload a media file (photo or video) to user profile.",
    responses={
        200: {"description": "File uploaded"},
        429: {"description": "Rate limit exceeded"},
    },
)
@inject
@limiter.limit("5/minute")
async def upload_file(
    request: Request,
    user_id: int = Depends(get_user_id_from_headers),
    file: UploadFile = File(..., description="The media file to upload."),
    type: MediaType = Form(..., description="Media file type (photo or video)."),
    media_service: MediaService = Depends(Provide[Container.services.provided.media]),
):
    logger.info(f"Uploading file: {file.filename} for user {user_id}")
    await media_service.upload_file(user_id, await file.read(), file.filename, type)
    logger.info(f"File uploaded: {file.filename} for user {user_id}")

@router.get(
    "/presigned-urls",
    response_model=GetPresignedUrlsResponse,
    tags=["Media"],
    summary="Get presigned media URLs",
    description="Retrieve presigned URLs for media files.",
    responses={
        200: {"description": "Presigned URLs generated"},
        429: {"description": "Rate limit exceeded"},
    },
)
@inject
@limiter.limit("10/minute")
async def get_presigned_urls(
    request: Request,
    user_id: int = Depends(get_user_id_from_headers),
    media_service: MediaService = Depends(Provide[Container.services.provided.media]),
):
    logger.info(f"Generating presigned URLs for user {user_id}")
    result = await media_service.generate_presigned_urls(user_id)
    logger.info(f"Presigned URLs generated for user {user_id}")
    return result

@router.delete(
    "/files",
    tags=["Media"],
    summary="Delete all user files",
    description="Delete all uploaded media files of the user.",
    responses={
        204: {"description": "Files deleted"},
        429: {"description": "Rate limit exceeded"},
    },
)
@inject
@limiter.limit("3/minute")
async def delete_files(
    request: Request,
    user_id: int = Depends(get_user_id_from_headers),
    media_service: MediaService = Depends(Provide[Container.services.provided.media]),
):
    logger.info(f"Deleting files for user {user_id}")
    await media_service.delete_files(user_id)
    logger.info(f"Files deleted for user {user_id}")
