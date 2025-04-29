from pydantic import BaseModel
from typing import Optional
from enum import Enum

class SwipeAction(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    QUESTION = "question"

class SwipeInput(BaseModel):
    from_user_id: int
    to_user_id: int
    action: SwipeAction
    message: Optional[str] = None
