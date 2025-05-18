from typing import Optional
from httpx import HTTPStatusError

from api.BaseApiClient import BaseApiClient
from models.api.profile.requests import SaveProfileRequest, UpdateFieldRequest, ToggleActiveRequest
from models.api.profile.responses import GetProfileResponse, SaveProfileResponse
from exceptions.rate_limit_error import RateLimitError

class ProfileClient(BaseApiClient):
    def __init__(self, base_url: str):
        super().__init__(base_url)

    async def _handle_response(self, resp, parse_model=None):
        """Общая обработка ответов, включая 404 и 429."""
        if resp.status_code == 404:
            return None
        elif resp.status_code == 429:
            raise RateLimitError("Слишком много запросов. Попробуйте позже.")
        resp.raise_for_status()
        return parse_model(**resp.json()) if parse_model else None

    async def save_profile(self, user_id: int, data: SaveProfileRequest) -> SaveProfileResponse:
        resp = await self.client.put(
            f"/profile",
            json=data.model_dump(),
            headers=self._headers(user_id)
        )
        return await self._handle_response(resp, SaveProfileResponse)

    async def get_profile_by_user_id(self, user_id: int) -> Optional[GetProfileResponse]:
        resp = await self.client.get(
            f"/profile",
            headers=self._headers(user_id)
        )
        return await self._handle_response(resp, GetProfileResponse)

    async def update_field(self, user_id: int, data: UpdateFieldRequest):
        resp = await self.client.patch(
            f"/profile",
            json=data.model_dump(mode='json'),
            headers=self._headers(user_id)
        )
        await self._handle_response(resp)

    async def toggle_active(self, user_id: int, data: ToggleActiveRequest):
        resp = await self.client.patch(
            f"/profile/active",
            json=data.model_dump(),
            headers=self._headers(user_id)
        )
        await self._handle_response(resp)

    async def verify_video(self, user_id: int, file_bytes: bytes, file_id: str):
        files = {'file': (f"{file_id}.mp4", file_bytes, 'video/mp4')}

        resp = await self.client.post(
            f"/profile/verify-video",
            files=files,
            headers=self._headers(user_id)
        )

        return await self._handle_response(resp)