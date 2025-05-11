from io import BytesIO

from infrastructure.storage.s3.s3_uploader import S3Uploader
from domain.media.repositories.media_repository import MediaRepository
from api.v1.schemas.media import MediaType, GetPresignedUrlsResponse, PresignedMedia

class MediaService:
    def __init__(self, uploader: S3Uploader, media_repo: MediaRepository):
        self.uploader = uploader
        self.media_repo = media_repo

    async def upload_file(self, user_id: int, file_bytes: bytes, filename: str, type: MediaType):
        byte_stream = BytesIO(file_bytes)
        key = await self.uploader.upload_file(byte_stream, filename, str(user_id))
        await self.media_repo.save_media(user_id, key, type.value)

    async def generate_presigned_urls(self, user_id: int) -> GetPresignedUrlsResponse:
        media_records = await self.media_repo.get_media_by_user_id(user_id)
        media_type_map = {record["s3_key"]: record["type"] for record in media_records}

        print('\n\n', media_type_map, '\n\n')

        keys_with_urls = self.uploader.generate_presigned_urls_for_folder(str(user_id))

        print('\n\n', keys_with_urls, '\n\n')

        presigned_media = []
        for s3_key, url in keys_with_urls:
            media_type = media_type_map.get(s3_key)
            presigned_media.append(PresignedMedia(url=url, type=MediaType(media_type)))
        
        return GetPresignedUrlsResponse(presigned_media=presigned_media)

    async def delete_files(self, user_id: int):
        await self.uploader.delete_folder(str(user_id))
        await self.media_repo.delete_media_by_user_id(user_id)
