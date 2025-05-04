from typing import Optional

from api.BaseApiClient import BaseApiClient
from models.api.recsys.responses import GetRecommendationsResponse

class RecSysClient(BaseApiClient):
    def __init__(self, base_url: str):
        super().__init__(base_url)

    async def get_recommendations(self, user_id: int, count: int = 30) -> Optional[GetRecommendationsResponse]:
        resp = await self.client.get(f"/recsys/users/recommendations", params={"count": count}, headers=self._headers(user_id))        
        resp.raise_for_status()
        return GetRecommendationsResponse(**resp.json())
