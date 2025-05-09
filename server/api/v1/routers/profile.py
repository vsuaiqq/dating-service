from fastapi import APIRouter, Request, Depends, UploadFile, File
from dependency_injector.wiring import inject, Provide
from slowapi import Limiter

from api.v1.dependecies.headers import get_user_id_from_headers
from api.v1.schemas.profile import SaveProfileRequest, UpdateFieldRequest, ToggleActiveRequest, GetProfileResponse, SaveProfileResponse
from domain.profile.services.profile_service import ProfileService
from di.container import Container
from shared.exceptions.exceptions import NotFoundException
from core.limiter import user_id_rate_key
from core.logger import logger

router = APIRouter()

limiter = Limiter(
    key_func=user_id_rate_key,
    storage_uri=Container.config().redis_url_limiter
)

@router.put("", response_model=SaveProfileResponse)
@inject
async def save_profile(
    request: Request,
    data: SaveProfileRequest,
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(Provide[Container.services.provided.profile])
):
    logger.info(f"Starting profile save for user {user_id}")
    result = await profile_service.save_profile(user_id, data)
    logger.info(f"Profile saved successfully for user {user_id}")
    return result

@router.get("", response_model=GetProfileResponse)
@limiter.limit("3/minute")
@inject
async def get_profile_by_user_id(
    request: Request,
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(Provide[Container.services.provided.profile])
):
    logger.info(f"Fetching profile for user {user_id}")
    result = await profile_service.get_profile_by_user_id(user_id)
    if result is None:
        logger.warning(f"Profile not found for user {user_id}")
        raise NotFoundException()
    logger.info(f"Profile retrieved successfully for user {user_id}")
    return result

@router.patch("")
@inject
async def update_field(
    request: Request,
    data: UpdateFieldRequest,
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(Provide[Container.services.provided.profile])
):
    logger.info(f"Updating field {data.field_name} for user {user_id}")
    await profile_service.update_field(user_id, data)
    logger.info(f"Field {data.field_name} updated successfully for user {user_id}")

@router.patch("/active")
@inject
async def toggle_active(
    request: Request,
    data: ToggleActiveRequest,
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(Provide[Container.services.provided.profile])
):
    logger.info(f"Toggling active status to {data.is_active} for user {user_id}")
    await profile_service.toggle_active(user_id, data)
    logger.info(f"Active status toggled successfully to {data.is_active} for user {user_id}")

@router.post("/verify-video")
@inject
async def verify_video(
    request: Request,
    user_id: int = Depends(get_user_id_from_headers),
    file: UploadFile = File(...),
    profile_service: ProfileService = Depends(Provide[Container.services.provided.profile])
):
    logger.info(f"Starting video verification for user {user_id}")
    profile_service.verify_video(user_id, await file.read())
    logger.info(f"Video verification completed for user {user_id}")
