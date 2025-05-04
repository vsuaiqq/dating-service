from typing import Optional
import httpx

class BaseApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url)

    def _headers(self, user_id: int, username: Optional[str] = None) -> dict:
        headers = {"X-User-ID": str(user_id)}
        headers["X-Telegram-Username"] = username if username is not None else ''
        return headers

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
