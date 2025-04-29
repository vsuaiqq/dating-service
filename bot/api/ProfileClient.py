import httpx
import json
from typing import List, Union

class ProfileClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url)

    async def save_profile(self, profile_data: dict) -> dict:
        resp = await self.client.post("/profile/save", json=profile_data)
        resp.raise_for_status()
        return resp.json()

    async def save_media(self, profile_id: int, media: List[dict]) -> dict:
        payload = {"profile_id": profile_id, "media": media}
        resp = await self.client.post("/profile/media/save", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def get_profile_by_user_id(self, user_id: int) -> dict:
        resp = await self.client.get(f"/profile/by_user/{user_id}")
        resp.raise_for_status()
        return resp.json()

    async def get_media_by_profile_id(self, profile_id: int) -> List[dict]:
        resp = await self.client.get(f"/profile/media/{profile_id}")
        resp.raise_for_status()
        return resp.json()

    async def toggle_active(self, user_id: int, is_active: bool) -> dict:
        payload = {"user_id": user_id, "is_active": is_active}
        resp = await self.client.post("/profile/toggle_active", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def update_field(self, user_id: int, field_name: str, value: Union[str, dict]) -> dict:
        payload = {"user_id": user_id, "field_name": field_name, "value": value}
        resp = await self.client.post("/profile/update_field", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def delete_media(self, profile_id: int):
        headers = httpx.Headers({"Content-Type": "application/json"})
        payload = json.dumps({"profile_id": profile_id})
        resp = await self.client.request(
            method="DELETE",
            url="/profile/media/delete",
            content=payload,
            headers=headers,
        )
        return resp

    async def close(self):
        await self.client.aclose()
