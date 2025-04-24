import httpx

class RecSysClient:
    def __init__(self, base_url: str, num_of_recs):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url)
        self.num_of_recs = num_of_recs

    async def get_recommendations(self, user_id: int, count: int = None) -> dict:
        if count is None:
            count = self.num_of_recs

        resp = await self.client.get(f"/recsys/recommendations/{user_id}", params={"count": 30})
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self.client.aclose()
