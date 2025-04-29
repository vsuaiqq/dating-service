from pydantic import BaseModel
from typing import Optional

class SwipeInput(BaseModel):
    from_user_id: int
    to_user_id: int
    action: str
    message: Optional[str] = None
