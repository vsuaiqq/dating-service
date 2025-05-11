from fastapi import APIRouter, Request, Depends, Query
from dependency_injector.wiring import inject, Provide
from slowapi import Limiter

from api.v1.deps.headers import get_user_id_from_headers
from api.v1.schemas.recommendation import GetRecommendationsResponse
from domain.recommendation.services.recommendation_service import RecommendationService
from di.container import Container
from core.limiter import get_user_id_rate_key
from core.logger import logger

router = APIRouter()

limiter = Limiter(
    key_func=get_user_id_rate_key,
    storage_uri=Container.config().redis_url_limiter
)

@router.get(
    "/users/recommendations",
    summary="Получить рекомендации",
    description="Возвращает список рекомендованных пользователей, основываясь на профиле пользователя.",
    tags=["Рекомендации"],
    response_model=GetRecommendationsResponse
)
@inject
@limiter.limit("10/minute")
async def get_recommendations(
    request: Request,
    count: int = Query(..., description="Количество запрашиваемых рекомендаций"),
    user_id: int = Depends(get_user_id_from_headers),
    recommendation_service: RecommendationService = Depends(Provide[Container.services.provided.recommendation])
):
    logger.info(
        f"Запрос рекомендаций для пользователя {user_id}, количество: {count}",
        extra={"user_id": user_id, "count": count}
    )

    result = await recommendation_service.get_recommendations(user_id, count)

    logger.info(
        f"Успешно получено {len(result.recommendations)} рекомендаций для пользователя {user_id}",
        extra={
            "user_id": user_id,
            "recommendations_count": len(result.recommendations)
        }
    )

    return result
