from pydantic import BaseModel
from typing import List

class MediaItem(BaseModel):
    type: str
    s3_key: str

class MediaList(BaseModel):
    profile_id: int
    media: List[MediaItem]
