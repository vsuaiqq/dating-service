from pydantic import BaseModel, Field
from typing import List

class RecommendationItem(BaseModel):
    user_id: int = Field(..., description="ID рекомендованного пользователя")
    distance: float = Field(..., description="Расстояние до пользователя в километрах")

class GetRecommendationsResponse(BaseModel):
    recommendations: List[RecommendationItem] = Field(
        ..., description="Список рекомендованных пользователей"
    )

    class Config:
        schema_extra = {
            "example": {
                "recommendations": [
                    {"user_id": 101, "distance": 2.5},
                    {"user_id": 205, "distance": 7.8},
                    {"user_id": 309, "distance": 12.0}
                ]
            }
        }
