from api.BaseApiClient import BaseApiClient
from models.api.media.responses import GetPresignedUrlsResponse

class MediaClient(BaseApiClient):
    def __init__(self, base_url: str):
        super().__init__(base_url)

    async def upload_file(self, user_id: int, type: str, file: bytes, filename: str):
        files = {'file': (filename, file)}
        data = {'type': type}
        resp = await self.client.post("/media/upload", files=files, data=data, headers=self._headers(user_id))
        resp.raise_for_status()

    async def get_presigned_urls(self, user_id: int) -> GetPresignedUrlsResponse:
        resp = await self.client.get("/media/presigned-urls", headers=self._headers(user_id))
        resp.raise_for_status()
        return GetPresignedUrlsResponse(**resp.json())

    async def delete_files(self, user_id: int):
        resp = await self.client.delete(f"/media/files", headers=self._headers(user_id))
        resp.raise_for_status()
