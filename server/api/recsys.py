from fastapi import APIRouter, Depends, HTTPException
from core.dependecies import get_recommendations_service, get_user_id_from_headers
from services.recsys.RecommendationsService import RecommendationsService
from models.api.recsys.responses import GetRecommendationsResponse
from core.logger import logger

router = APIRouter()


@router.get("/users/recommendations", response_model=GetRecommendationsResponse)
async def get_recommendations(
        count: int,
        user_id: int = Depends(get_user_id_from_headers),
        recommendations_service: RecommendationsService = Depends(get_recommendations_service)
):
    try:
        logger.info(
            f"Starting to get recommendations for user {user_id}, count: {count}",
            extra={"user_id": user_id, "count": count}
        )

        result = await recommendations_service.get_recommendations(user_id, count)

        logger.info(
            f"Successfully got {len(result.recommendations)} recommendations for user {user_id}",
            extra={
                "user_id": user_id,
                "recommendations_count": len(result.recommendations)
            }
        )

        return result

    except Exception as e:
        logger.error(
            f"Failed to get recommendations for user {user_id}: {str(e)}",
            exc_info=True,
            extra={"user_id": user_id, "error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))