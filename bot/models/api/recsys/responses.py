from pydantic import BaseModel
from typing import List

class RecommendationItem(BaseModel):
    user_id: int
    distance: float

class GetRecommendationsResponse(BaseModel):
    recommendations: List[RecommendationItem]
