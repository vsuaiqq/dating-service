from pydantic import BaseModel, Field
from typing import List

class RecommendationItem(BaseModel):
    user_id: int = Field(..., description="ID of the recommended user")
    distance: float = Field(..., description="Distance to the user in kilometers")

class GetRecommendationsResponse(BaseModel):
    recommendations: List[RecommendationItem] = Field(
        ..., description="List of recommended users"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "recommendations": [
                    {"user_id": 101, "distance": 2.5},
                    {"user_id": 205, "distance": 7.8},
                    {"user_id": 309, "distance": 12.0}
                ]
            }
        }
    }
