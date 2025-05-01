import httpx
from models.swipe.requests import AddSwipeRequest

class SwipeClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url)

    async def add_swipe(self, swipe_data: AddSwipeRequest) -> None:
        resp = await self.client.post("/swipe", json=swipe_data.model_dump())
        resp.raise_for_status()

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
