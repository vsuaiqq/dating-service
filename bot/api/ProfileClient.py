from typing import Optional

from api.BaseApiClient import BaseApiClient
from models.api.profile.requests import SaveProfileRequest, UpdateFieldRequest, ToggleActiveRequest
from models.api.profile.responses import GetProfileResponse, SaveProfileResponse

class ProfileClient(BaseApiClient):
    def __init__(self, base_url: str):
        super().__init__(base_url)

    async def save_profile(self, user_id: int, data: SaveProfileRequest) -> SaveProfileResponse:
        resp = await self.client.put(f"/profile", json=data.model_dump(), headers=self._headers(user_id))
        resp.raise_for_status()
        return SaveProfileResponse(**resp.json())

    async def get_profile_by_user_id(self, user_id: int) -> Optional[GetProfileResponse]:
        resp = await self.client.get(f"/profile", headers=self._headers(user_id))
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return GetProfileResponse(**resp.json())

    async def update_field(self, user_id: int, data: UpdateFieldRequest):
        resp = await self.client.patch(f"/profile", json=data.model_dump(mode='json'), headers=self._headers(user_id))
        resp.raise_for_status()

    async def toggle_active(self, user_id: int, data: ToggleActiveRequest):
        resp = await self.client.patch(f"/profile/active", json=data.model_dump(), headers=self._headers(user_id))
        resp.raise_for_status()

    async def verify_video(self, user_id: int, file_bytes: bytes, file_id: str):
        files = {'file': (f"{file_id}.mp4", file_bytes, 'video/mp4')}
        resp = await self.client.post(f"/profile/verify-video", files=files, headers=self._headers(user_id))
        resp.raise_for_status()
