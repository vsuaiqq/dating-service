from fastapi import APIRouter, Depends, HTTPException

from core.dependecies import get_recommendations_service
from services.recsys.RecommendationsService import RecommendationsService
from models.recsys.responses import GetRecommendationsResponse

router = APIRouter()

@router.get("/users/{user_id}/recommendations", response_model=GetRecommendationsResponse)
async def get_recommendations(
    user_id: int,
    count: int,
    recommendations_service: RecommendationsService = Depends(get_recommendations_service)
):
    try:
        return await recommendations_service.get_recommendations(user_id, count)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
