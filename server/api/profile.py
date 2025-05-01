from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from core.dependecies import get_profile_service
from services.profile.ProfileService import ProfileService
from models.profile.requests import SaveProfileRequest, SaveMediaRequest, ToggleActiveRequest, UpdateFieldRequest
from models.profile.responses import SaveProfileResponse, GetProfileResponse, GetMediaResponse

router = APIRouter()

@router.put("/{user_id}", response_model=SaveProfileResponse)
async def save_profile(
    user_id: int,
    data: SaveProfileRequest,
    profile_service: ProfileService = Depends(get_profile_service)
):
    try:
        return await profile_service.save_profile(user_id, data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}", response_model=GetProfileResponse)
async def get_profile_by_user_id(
    user_id: int,
    profile_service: ProfileService = Depends(get_profile_service)
):
    result = await profile_service.get_profile_by_user_id(user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return result

@router.patch("/{user_id}")
async def update_field(
    user_id: int,
    data: UpdateFieldRequest, 
    profile_service: ProfileService = Depends(get_profile_service)
):
    try:
        await profile_service.update_field(user_id, data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{user_id}/active")
async def toggle_active(
    user_id: int,
    data: ToggleActiveRequest, 
    profile_service: ProfileService = Depends(get_profile_service)
):
    try:
        await profile_service.toggle_active(user_id, data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}/verify-video")
async def verify_video(
    user_id: int,
    file: UploadFile = File(...),
    profile_service: ProfileService = Depends(get_profile_service)
):
    try:
        profile_service.verify_video(user_id, await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}/media")
async def save_media(
    user_id: int,
    data: SaveMediaRequest, 
    profile_service: ProfileService = Depends(get_profile_service)
):
    try:
        await profile_service.save_media(user_id, data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/media", response_model=GetMediaResponse)
async def get_media_by_profile_id(
    user_id: int,
    profile_service: ProfileService = Depends(get_profile_service)
):
    try:
        return await profile_service.get_media_by_profile_id(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}/media")
async def delete_media(
    user_id: int,
    profile_service: ProfileService = Depends(get_profile_service)
):
    try:
        await profile_service.delete_media(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
