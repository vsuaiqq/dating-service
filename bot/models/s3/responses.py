from pydantic import BaseModel

class UploadFileResponse(BaseModel):
    key: str

class GetPresignedUrlResponse(BaseModel):
    url: str
