from enum import Enum
from pydantic import BaseModel, Field
from typing import List

class MediaType(str, Enum):
    photo = "photo"
    video = "video"

class PresignedMedia(BaseModel):
    url: str = Field(..., description="Presigned URL for uploading the file")
    type: MediaType = Field(..., description="Type of media file: photo or video")

class GetPresignedUrlsResponse(BaseModel):
    presigned_media: List[PresignedMedia] = Field(..., description="List of presigned URLs for uploading media files")

    model_config = {
        "json_schema_extra": {
            "example": {
                "presigned_media": [
                    {
                        "url": "https://example-bucket.s3.amazonaws.com/upload/photo1.jpg?X-Amz-Signature=abc123...",
                        "type": "photo"
                    },
                    {
                        "url": "https://example-bucket.s3.amazonaws.com/upload/video1.mp4?X-Amz-Signature=def456...",
                        "type": "video"
                    }
                ]
            }
        }
    }
