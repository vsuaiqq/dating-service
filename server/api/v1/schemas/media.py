from enum import Enum
from pydantic import BaseModel
from typing import List

class MediaType(str, Enum):
    photo = "photo"
    video = "video"

class PresignedMedia(BaseModel):
    url: str
    type: MediaType

class GetPresignedUrlsResponse(BaseModel):
    presigned_media: List[PresignedMedia]
