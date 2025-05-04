from api.BaseApiClient import BaseApiClient
from models.api.media.responses import UploadFileResponse, GetPresignedUrlResponse

class MediaClient(BaseApiClient):
    def __init__(self, base_url: str):
        super().__init__(base_url)

    async def upload_file(self, file: bytes, filename: str) -> UploadFileResponse:
        files = {'file': (filename, file)}
        resp = await self.client.post("/media/upload", files=files)
        resp.raise_for_status()
        return UploadFileResponse(**resp.json())

    async def get_presigned_url(self, key: str, expiration: int = 3600) -> GetPresignedUrlResponse:
        params = {"key": key, "expiration": expiration}
        resp = await self.client.get("/media/presigned-url", params=params)
        resp.raise_for_status()
        return GetPresignedUrlResponse(**resp.json())

    async def delete_file(self, key: str):
        resp = await self.client.delete(f"/media/files/{key}")
        resp.raise_for_status()
