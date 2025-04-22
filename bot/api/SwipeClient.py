import httpx
from typing import Optional, Literal

class SwipeClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url)

    async def add_swipe(
        self,
        from_user_id: int,
        to_user_id: int,
        action: Literal["like", "dislike", "question"],
        message: Optional[str] = None
    ) -> dict:
        payload = {
            "from_user_id": from_user_id,
            "to_user_id": to_user_id,
            "action": action,
            "message": message
        }
        resp = await self.client.post("/swipe/add", json=payload)
        resp.raise_for_status()
        return resp.json()
