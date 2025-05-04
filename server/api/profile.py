from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from core.dependecies import get_profile_service, get_user_id_from_headers
from services.profile.ProfileService import ProfileService
from models.api.profile.requests import SaveProfileRequest, SaveMediaRequest, ToggleActiveRequest, UpdateFieldRequest
from models.api.profile.responses import SaveProfileResponse, GetProfileResponse, GetMediaResponse
from core.logger import logger
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
    try:
        logger.info(f"Fetching profile for user {user_id}")
        result = await profile_service.get_profile_by_user_id(user_id)
        if result is None:
            logger.warning(f"Profile not found for user {user_id}")
            raise HTTPException(status_code=404, detail="Profile not found")
        logger.info(f"Profile retrieved successfully for user {user_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to fetch profile for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("")
async def update_field(
    data: UpdateFieldRequest,
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(get_profile_service)
):
    try:
        logger.info(f"Updating field {data.field} for user {user_id}")
        await profile_service.update_field(user_id, data)
        logger.info(f"Field {data.field} updated successfully for user {user_id}")
        return {"status": "success", "message": f"Field {data.field} updated"}
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
        return {"status": "success", "message": f"Active status set to {data.is_active}"}
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
        return {"status": "success", "message": "Video verification started"}
    except Exception as e:
        logger.error(f"Video verification failed for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/media")
async def save_media(
    data: SaveMediaRequest,
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(get_profile_service)
):
    try:
        logger.info(f"Saving media for user {user_id}")
        await profile_service.save_media(user_id, data)
        logger.info(f"Media saved successfully for user {user_id}")
        return {"status": "success", "message": "Media saved"}
    except Exception as e:
        logger.error(f"Failed to save media for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/media", response_model=GetMediaResponse)
async def get_media_by_profile_id(
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(get_profile_service)
):
    try:
        logger.info(f"Fetching media for user {user_id}")
        result = await profile_service.get_media_by_profile_id(user_id)
        logger.info(f"Media retrieved successfully for user {user_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to fetch media for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/media")
async def delete_media(
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(get_profile_service)
):
    try:
        logger.info(f"Deleting media for user {user_id}")
        await profile_service.delete_media(user_id)
        logger.info(f"Media deleted successfully for user {user_id}")
        return {"status": "success", "message": "Media deleted"}
    except Exception as e:
        logger.error(f"Failed to delete media for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))