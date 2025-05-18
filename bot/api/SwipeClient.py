from typing import Optional
from httpx import HTTPStatusError
from api.BaseApiClient import BaseApiClient
from models.api.swipe.requests import AddSwipeRequest
from exceptions.rate_limit_error import RateLimitError


class SwipeClient(BaseApiClient):
    def __init__(self, base_url: str):
        super().__init__(base_url)

    async def _handle_response(self, resp, parse_model=None):
        """Общая обработка ответов, включая 404 и 429."""
        if resp.status_code == 404:
            return None
        elif resp.status_code == 429:
            raise RateLimitError(
                message="Слишком много свайпов. Попробуйте позже."
            )
        resp.raise_for_status()
        return parse_model(**resp.json()) if parse_model else resp

    async def add_swipe(
            self,
            user_id: int,
            swipe_data: AddSwipeRequest,
            username: Optional[str] = None
    ):

        resp = await self.client.post(
            "/swipe",
            json=swipe_data.model_dump(),
            headers=self._headers(user_id, username)
        )
        return await self._handle_response(resp)