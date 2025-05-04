from typing import Optional

from api.BaseApiClient import BaseApiClient
from models.api.swipe.requests import AddSwipeRequest

class SwipeClient(BaseApiClient):
    def __init__(self, base_url: str):
        super().__init__(base_url)

    async def add_swipe(self, user_id: int, username: Optional[str], swipe_data: AddSwipeRequest):
        resp = await self.client.post("/swipe", json=swipe_data.model_dump(), headers=self._headers(user_id, username))
        resp.raise_for_status()
