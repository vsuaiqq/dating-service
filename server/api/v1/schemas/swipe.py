from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class SwipeAction(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    QUESTION = "question"

class AddSwipeRequest(BaseModel):
    from_user_id: int = Field(..., description="ID of the user performing the swipe")
    to_user_id: int = Field(..., description="ID of the user being swiped on")
    action: SwipeAction = Field(..., description="Action type: like, dislike, or question")
    message: Optional[str] = Field(None, description="Optional message for the user")

    model_config = {
        "json_schema_extra": {
            "example": {
                "from_user_id": 123,
                "to_user_id": 456,
                "action": "like",
                "message": "Hi! Would you like to connect?"
            }
        }
    }
