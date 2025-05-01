from pydantic import BaseModel
from typing import List

class GetRecommendationsResponse(BaseModel):
    recommendations: List[int]
