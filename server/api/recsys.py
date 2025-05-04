from fastapi import APIRouter, Depends, HTTPException

from core.dependecies import get_recommendations_service, get_user_id_from_headers
from services.recsys.RecommendationsService import RecommendationsService
from models.api.recsys.responses import GetRecommendationsResponse

router = APIRouter()

@router.get("/users/recommendations", response_model=GetRecommendationsResponse)
async def get_recommendations(
    count: int,
    user_id: int = Depends(get_user_id_from_headers),
    recommendations_service: RecommendationsService = Depends(get_recommendations_service)
):
    try:
        return await recommendations_service.get_recommendations(user_id, count)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
