import httpx

class RecSysClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url)

    async def get_recommendations(self, user_id: int) -> dict:
        resp = await self.client.get(f"/recsys/recommendations/{user_id}")
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self.client.aclose()
