import httpx
from typing import Optional
from models.recsys.responses import GetRecommendationsResponse

class RecSysClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url)

    async def get_recommendations(self, user_id: int, count: int = 30) -> Optional[GetRecommendationsResponse]:
        resp = await self.client.get(f"/recsys/users/{user_id}/recommendations", params={"count": count})        
        resp.raise_for_status()
        return GetRecommendationsResponse(**resp.json())

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
