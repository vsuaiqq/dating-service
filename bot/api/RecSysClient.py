from typing import Optional

from api.BaseApiClient import BaseApiClient
from models.api.recsys.responses import GetRecommendationsResponse
from exceptions.rate_limit_error import RateLimitError  # Импорт нашего исключения


class RecSysClient(BaseApiClient):
    def __init__(self, base_url: str):
        super().__init__(base_url)

    async def get_recommendations(self, user_id: int, count: int = 30) -> Optional[GetRecommendationsResponse]:
        try:
            resp = await self.client.get(
                f"/recsys/users/recommendations",
                params={"count": count},
                headers=self._headers(user_id)
            )

            if resp.status_code == 429:
                raise RateLimitError("Rate limit exceeded")

            resp.raise_for_status()
            return GetRecommendationsResponse(**resp.json())
        except RateLimitError:
            raise
        except Exception as e:
            raise

        except Exception as e:
            raise