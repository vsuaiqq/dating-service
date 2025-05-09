from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide

from api.v1.dependecies.headers import get_user_id_from_headers
from api.v1.schemas.recommendation import GetRecommendationsResponse
from domain.recommendation.services.recommendation_service import RecommendationService
from di.container import Container
from core.logger import logger

router = APIRouter()

@router.get("/users/recommendations", response_model=GetRecommendationsResponse)
@inject
async def get_recommendations(
    count: int,
    user_id: int = Depends(get_user_id_from_headers),
    recommendation_service: RecommendationService = Depends(Provide[Container.services.provided.recommendation])
):
    logger.info(
        f"Starting to get recommendations for user {user_id}, count: {count}",
        extra={"user_id": user_id, "count": count}
    )

    result = await recommendation_service.get_recommendations(user_id, count)

    logger.info(
        f"Successfully got {len(result.recommendations)} recommendations for user {user_id}",
        extra={
            "user_id": user_id,
            "recommendations_count": len(result.recommendations)
        }
    )

    return result
