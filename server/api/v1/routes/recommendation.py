from fastapi import APIRouter, Request, Depends, Query
from dependency_injector.wiring import inject, Provide
from slowapi import Limiter

from api.v1.deps.headers import get_user_id_from_headers
from api.v1.schemas.recommendation import GetRecommendationsResponse
from domain.recommendation.services.recommendation_service import RecommendationService
from di.container import Container
from core.limiter import get_user_id_rate_key

router = APIRouter()

limiter = Limiter(
    key_func=get_user_id_rate_key,
    storage_uri=Container.config().redis_url_limiter
)

@router.get(
    "/users/recommendations",
    response_model=GetRecommendationsResponse,
    tags=["Recommendations"],
    summary="Get user recommendations",
    description="Return a list of recommended users based on the requesting user's profile.",
    responses={
        200: {"description": "Recommendations retrieved"},
        429: {"description": "Rate limit exceeded"},
    },
)
@inject
@limiter.limit("10/minute")
async def get_recommendations(
    request: Request,
    count: int = Query(..., description="Number of recommendations to retrieve."),
    user_id: int = Depends(get_user_id_from_headers),
    recommendation_service: RecommendationService = Depends(Provide[Container.services.provided.recommendation])
):
    return await recommendation_service.get_recommendations(user_id, count)
