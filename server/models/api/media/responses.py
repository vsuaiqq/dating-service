from pydantic import BaseModel
from typing import List

from models.api.media.requests import MediaType

class PresignedMedia(BaseModel):
    url: str
    type: MediaType

class GetPresignedUrlsResponse(BaseModel):
    presigned_media: List[PresignedMedia]
