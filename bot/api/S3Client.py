import httpx
from models.s3.responses import UploadFileResponse, GetPresignedUrlResponse

class S3Client:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url)

    async def upload_file(self, file: bytes, filename: str) -> UploadFileResponse:
        files = {'file': (filename, file)}
        resp = await self.client.post("/s3/upload", files=files)
        resp.raise_for_status()
        return UploadFileResponse(**resp.json())

    async def get_presigned_url(self, key: str, expiration: int = 3600) -> GetPresignedUrlResponse:
        params = {"key": key, "expiration": expiration}
        resp = await self.client.get("/s3/presigned-url", params=params)
        resp.raise_for_status()
        return GetPresignedUrlResponse(**resp.json())

    async def delete_file(self, key: str):
        resp = await self.client.delete(f"/s3/files/{key}")
        resp.raise_for_status()

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
