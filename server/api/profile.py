from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from core.dependecies import get_profile_service, get_user_id_from_headers
from services.profile.ProfileService import ProfileService
from models.api.profile.requests import SaveProfileRequest, SaveMediaRequest, ToggleActiveRequest, UpdateFieldRequest
from models.api.profile.responses import SaveProfileResponse, GetProfileResponse, GetMediaResponse

router = APIRouter()

@router.put("", response_model=SaveProfileResponse)
async def save_profile(
    data: SaveProfileRequest,
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(get_profile_service)
):
    try:
        return await profile_service.save_profile(user_id, data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=GetProfileResponse)
async def get_profile_by_user_id(
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(get_profile_service)
):
    result = await profile_service.get_profile_by_user_id(user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return result

@router.patch("")
async def update_field(
    data: UpdateFieldRequest, 
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(get_profile_service)
):
    try:
        await profile_service.update_field(user_id, data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/active")
async def toggle_active(
    data: ToggleActiveRequest, 
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(get_profile_service)
):
    try:
        await profile_service.toggle_active(user_id, data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-video")
async def verify_video(
    user_id: int = Depends(get_user_id_from_headers),
    file: UploadFile = File(...),
    profile_service: ProfileService = Depends(get_profile_service)
):
    try:
        profile_service.verify_video(user_id, await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/media")
async def save_media(
    data: SaveMediaRequest,
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(get_profile_service)
):
    try:
        await profile_service.save_media(user_id, data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/media", response_model=GetMediaResponse)
async def get_media_by_profile_id(
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(get_profile_service)
):
    try:
        return await profile_service.get_media_by_profile_id(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/media")
async def delete_media(
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(get_profile_service)
):
    try:
        await profile_service.delete_media(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
