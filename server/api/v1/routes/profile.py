from fastapi import APIRouter, Request, Depends, UploadFile, File
from dependency_injector.wiring import inject, Provide
from slowapi import Limiter

from api.v1.deps.headers import get_user_id_from_headers
from api.v1.schemas.profile import (
    SaveProfileRequest,
    UpdateFieldRequest,
    ToggleActiveRequest,
    GetProfileResponse,
    SaveProfileResponse,
)
from domain.profile.services.profile_service import ProfileService
from di.container import Container
from shared.exceptions.exceptions import NotFoundException
from core.limiter import get_user_id_rate_key

router = APIRouter()

limiter = Limiter(
    key_func=get_user_id_rate_key,
    storage_uri=Container.config().redis_url_limiter
)

@router.put(
    "",
    response_model=SaveProfileResponse,
    tags=["Profile"],
    summary="Save profile",
    description="Save or update the profile of the authenticated user.",
    responses={
        200: {"description": "Profile successfully saved"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    },
)
@inject
@limiter.limit("5/minute")
async def save_profile(
    request: Request,
    data: SaveProfileRequest,
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(Provide[Container.services.provided.profile]),
):
    return await profile_service.save_profile(user_id, data)

@router.get(
    "",
    response_model=GetProfileResponse,
    tags=["Profile"],
    summary="Get profile by user ID",
    description="Retrieve the profile of the authenticated user.",
    responses={
        200: {"description": "Profile retrieved"},
        404: {"description": "Profile not found"},
        429: {"description": "Rate limit exceeded"},
    },
)
@inject
@limiter.limit("25/minute")
async def get_profile_by_user_id(
    request: Request,
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(Provide[Container.services.provided.profile]),
):
    result = await profile_service.get_profile_by_user_id(user_id)
    if result is None:
        raise NotFoundException()
    return result

@router.patch(
    "",
    tags=["Profile"],
    summary="Update profile field",
    description="Update a single field in the user's profile.",
    responses={
        204: {"description": "Field updated successfully"},
        429: {"description": "Rate limit exceeded"},
    },
)
@inject
@limiter.limit("10/minute")
async def update_field(
    request: Request,
    data: UpdateFieldRequest,
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(Provide[Container.services.provided.profile]),
):
    await profile_service.update_field(user_id, data)

@router.patch(
    "/active",
    tags=["Profile"],
    summary="Toggle profile active status",
    description="Activate or deactivate the user's profile.",
    responses={
        204: {"description": "Profile status updated"},
        429: {"description": "Rate limit exceeded"},
    },
)
@inject
@limiter.limit("10/minute")
async def toggle_active(
    request: Request,
    data: ToggleActiveRequest,
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(Provide[Container.services.provided.profile]),
):
    await profile_service.toggle_active(user_id, data)

@router.post(
    "/verify-video",
    tags=["Profile"],
    summary="Verify profile video",
    description="Upload a video file to verify the user's identity.",
    responses={
        200: {"description": "Video verification completed"},
        429: {"description": "Rate limit exceeded"},
    },
)
@inject
@limiter.limit("3/minute")
async def verify_video(
    request: Request,
    user_id: int = Depends(get_user_id_from_headers),
    file: UploadFile = File(..., description="Video file for verification"),
    profile_service: ProfileService = Depends(Provide[Container.services.provided.profile]),
):
    profile_service.verify_video(user_id, await file.read())
