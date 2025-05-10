from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class SwipeAction(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    QUESTION = "question"

class AddSwipeRequest(BaseModel):
    from_user_id: int = Field(..., description="ID пользователя, совершающего свайп")
    to_user_id: int = Field(..., description="ID пользователя, к которому направлен свайп")
    action: SwipeAction = Field(..., description="Тип действия: like, dislike или question")
    message: Optional[str] = Field(None, description="Необязательное сообщение для пользователя")

    class Config:
        schema_extra = {
            "example": {
                "from_user_id": 123,
                "to_user_id": 456,
                "action": "like",
                "message": "Привет! Хочешь познакомиться?"
            }
        }
