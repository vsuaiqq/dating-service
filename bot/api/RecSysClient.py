from typing import Optional
from httpx import HTTPStatusError
from api.BaseApiClient import BaseApiClient
from models.api.recsys.responses import GetRecommendationsResponse
from exceptions.rate_limit_error import RateLimitError


class RecSysClient(BaseApiClient):
    def __init__(self, base_url: str):
        super().__init__(base_url)

    async def _handle_response(self, resp, parse_model=None):
        if resp.status_code == 429:
            raise RateLimitError(
                message="Recommendations rate limit exceeded"
            )

        if resp.status_code == 404:
            return None

        resp.raise_for_status()
        return parse_model(**resp.json()) if parse_model else resp

    async def get_recommendations(
            self,
            user_id: int,
            count: int = 30
    ) -> Optional[GetRecommendationsResponse]:
        resp = await self.client.get(
            "/recsys/users/recommendations",
            params={"count": count},
            headers=self._headers(user_id)
        )
        return await self._handle_response(resp, GetRecommendationsResponse)