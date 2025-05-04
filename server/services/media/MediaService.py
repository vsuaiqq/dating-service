from io import BytesIO

from storage.S3Uploader import S3Uploader
from models.api.media.responses import UploadFileResponse, GetPresignedUrlResponse

class MediaService:
    def __init__(self, uploader: S3Uploader):
        self.uploader = uploader

    async def upload_file(self, file_bytes: bytes, filename: str) -> UploadFileResponse:
        byte_stream = BytesIO(file_bytes)
        key = await self.uploader.upload_file(byte_stream, filename)
        return UploadFileResponse(key=key)

    def generate_presigned_url(self, key: str, expiration: int) -> GetPresignedUrlResponse:
        url = self.uploader.generate_presigned_url(key, expiration)
        return GetPresignedUrlResponse(url=url)

    async def delete_file(self, key: str):
        await self.uploader.delete_file_by_key(key)
