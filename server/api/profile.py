from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from core.dependecies import get_profile_service, get_user_id_from_headers
from core.logger import logger
from services.profile.ProfileService import ProfileService
from models.api.profile.requests import SaveProfileRequest, ToggleActiveRequest, UpdateFieldRequest
from models.api.profile.responses import SaveProfileResponse, GetProfileResponse

router = APIRouter()

@router.put("", response_model=SaveProfileResponse)
async def save_profile(
    data: SaveProfileRequest,
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(get_profile_service)
):
    try:
        logger.info(f"Starting profile save for user {user_id}")
        result = await profile_service.save_profile(user_id, data)
        logger.info(f"Profile saved successfully for user {user_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to save profile for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=GetProfileResponse)
async def get_profile_by_user_id(
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(get_profile_service)
):
    logger.info(f"Fetching profile for user {user_id}")
    result = await profile_service.get_profile_by_user_id(user_id)
    if result is None:
        logger.warning(f"Profile not found for user {user_id}")
        raise HTTPException(status_code=404, detail="Profile not found")
    logger.info(f"Profile retrieved successfully for user {user_id}")
    return result

@router.patch("")
async def update_field(
    data: UpdateFieldRequest,
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(get_profile_service)
):
    try:
        logger.info(f"Updating field {data.field_name} for user {user_id}")
        await profile_service.update_field(user_id, data)
        logger.info(f"Field {data.field_name} updated successfully for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to update field {data.field} for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/active")
async def toggle_active(
    data: ToggleActiveRequest,
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(get_profile_service)
):
    try:
        logger.info(f"Toggling active status to {data.is_active} for user {user_id}")
        await profile_service.toggle_active(user_id, data)
        logger.info(f"Active status toggled successfully to {data.is_active} for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to toggle active status for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-video")
async def verify_video(
    user_id: int = Depends(get_user_id_from_headers),
    file: UploadFile = File(...),
    profile_service: ProfileService = Depends(get_profile_service)
):
    try:
        logger.info(f"Starting video verification for user {user_id}")
        profile_service.verify_video(user_id, await file.read())
        logger.info(f"Video verification completed for user {user_id}")
    except Exception as e:
        logger.error(f"Video verification failed for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
