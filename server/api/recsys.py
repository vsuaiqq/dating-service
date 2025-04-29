from fastapi import APIRouter, Depends, HTTPException

from recsys.recsys import EmbeddingRecommender
from core.dependecies import get_recommender

router = APIRouter()

@router.get("/recommendations/{user_id}")
async def get_recommendations(user_id: int, count: int = 10, recommender: EmbeddingRecommender = Depends(get_recommender)):
    try:
        recommendations = await recommender.get_hybrid_recommendations(user_id=user_id, count=count)
        return {"recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
