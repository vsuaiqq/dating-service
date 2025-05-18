from typing import Optional
from httpx import HTTPStatusError
from api.BaseApiClient import BaseApiClient
from models.api.media.responses import GetPresignedUrlsResponse
from exceptions.rate_limit_error import RateLimitError


class MediaClient(BaseApiClient):
    def __init__(self, base_url: str):
        super().__init__(base_url)

    async def _handle_response(self, resp, parse_model=None):
        if resp.status_code == 404:
            return None
        elif resp.status_code == 429:
            retry_after = resp.headers.get('Retry-After', '1')
            raise RateLimitError(
                message="Слишком много запросов. Попробуйте позже."
            )
        resp.raise_for_status()
        return parse_model(**resp.json()) if parse_model else resp

    async def upload_file(
            self,
            user_id: int,
            file_type: str,
            file: bytes,
            filename: str,
            timeout: float = 30.0
    ):
        files = {'file': (filename, file)}
        data = {'type': file_type}

        resp = await self.client.post(
            "/media/upload",
            files=files,
            data=data,
            headers=self._headers(user_id),
            timeout=timeout
        )
        return await self._handle_response(resp)

    async def get_presigned_urls(
            self,
            user_id: int,
            timeout: float = 10.0
    ) -> GetPresignedUrlsResponse:
        resp = await self.client.get(
            "/media/presigned-urls",
            headers=self._headers(user_id),
            timeout=timeout
        )
        return await self._handle_response(resp, GetPresignedUrlsResponse)

    async def delete_files(
            self,
            user_id: int,
            timeout: float = 10.0
    ):
        resp = await self.client.delete(
            "/media/files",
            headers=self._headers(user_id),
            timeout=timeout
        )
        await self._handle_response(resp)