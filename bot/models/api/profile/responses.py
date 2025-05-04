from pydantic import BaseModel
from typing import Optional, List

class SaveProfileResponse(BaseModel):
    profile_id: int

class GetProfileResponse(BaseModel):
    user_id: int
    name: str
    gender: str
    city: Optional[str]
    age: int
    interesting_gender: str
    about: Optional[str]
    is_active: bool

class MediaItem(BaseModel):
    type: str
    s3_key: str

class GetMediaResponse(BaseModel):
    media: List[MediaItem]
