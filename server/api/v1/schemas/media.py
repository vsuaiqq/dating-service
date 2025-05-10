from enum import Enum
from pydantic import BaseModel, Field
from typing import List

class MediaType(str, Enum):
    photo = "photo"
    video = "video"

class PresignedMedia(BaseModel):
    url: str = Field(..., description="Предподписанный URL для загрузки файла")
    type: MediaType = Field(..., description="Тип медиафайла: фото или видео")

class GetPresignedUrlsResponse(BaseModel):
    presigned_media: List[PresignedMedia] = Field(..., description="Список URL-ов для загрузки медиафайлов")

    class Config:
        schema_extra = {
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
