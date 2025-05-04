from pydantic import BaseModel
from typing import Literal, Optional

class VideoValidationResultEvent(BaseModel):
    user_id: int
    is_human: bool

class LocationResolveResultEvent(BaseModel):
    user_id: int
    status: Literal['success', 'failed', 'waited']
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class SwipeEvent(BaseModel):
    from_username: str
    from_user_id: int
    to_user_id: int
    action: Literal['like', 'question']
    message: Optional[str] = None
