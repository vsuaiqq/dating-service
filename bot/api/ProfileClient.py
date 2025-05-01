import httpx
from typing import Optional

from models.profile.requests import SaveMediaRequest, SaveProfileRequest, UpdateFieldRequest, ToggleActiveRequest
from models.profile.responses import GetMediaResponse, GetProfileResponse, SaveProfileResponse

class ProfileClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url)

    async def save_profile(self, user_id: int, data: SaveProfileRequest) -> SaveProfileResponse:
        resp = await self.client.put(f"/profile/{user_id}", json=data.model_dump())
        resp.raise_for_status()
        return SaveProfileResponse(**resp.json())

    async def get_profile_by_user_id(self, user_id: int) -> Optional[GetProfileResponse]:
        resp = await self.client.get(f"/profile/{user_id}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return GetProfileResponse(**resp.json())

    async def update_field(self, user_id: int, data: UpdateFieldRequest):
        resp = await self.client.patch(f"/profile/{user_id}", json=data.model_dump())
        resp.raise_for_status()

    async def toggle_active(self, user_id: int, data: ToggleActiveRequest):
        resp = await self.client.patch(f"/profile/{user_id}/active", json=data.model_dump())
        resp.raise_for_status()

    async def verify_video(self, user_id: int, file_bytes: bytes, file_id: str):
        files = {'file': (f"{file_id}.mp4", file_bytes, 'video/mp4')}
        resp = await self.client.post(f"/profile/{user_id}/verify-video", files=files)
        resp.raise_for_status()

    async def save_media(self, user_id: int, data: SaveMediaRequest):
        resp = await self.client.post(f"/profile/{user_id}/media", json=data.model_dump())
        resp.raise_for_status()

    async def get_media_by_profile_id(self, user_id: int) -> GetMediaResponse:
        resp = await self.client.get(f"/profile/{user_id}/media")
        resp.raise_for_status()
        return GetMediaResponse(**resp.json())

    async def delete_media(self, user_id: int):
        resp = await self.client.delete(f"/profile/{user_id}/media")
        resp.raise_for_status()

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
