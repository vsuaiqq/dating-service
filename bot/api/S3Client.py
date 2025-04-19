import httpx
from typing import Optional


class S3Client:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url)

    async def upload_file(self, file_bytes: bytes, filename: str) -> dict:
        files = {"file": (filename, file_bytes)}
        resp = await self.client.post("/s3/upload", files=files)
        resp.raise_for_status()
        return resp.json()

    async def get_presigned_url(self, key: str, expiration: Optional[int] = 3600) -> dict:
        params = {"key": key, "expiration": expiration}
        resp = await self.client.get("/s3/url", params=params)
        resp.raise_for_status()
        return resp.json()

    async def delete_file(self, key: str) -> dict:
        data = {"key": key}
        resp = await self.client.request("DELETE", "/s3/delete", data=data)
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self.client.aclose()
