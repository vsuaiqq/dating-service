from io import BytesIO

from infrastructure.s3.uploader import S3Uploader
from domain.media.repositories.media_repository import MediaRepository
from domain.profile.repositories.profile_repository import ProfileRepository
from api.v1.schemas.media import MediaType, GetPresignedUrlsResponse, PresignedMedia

class MediaService:
    def __init__(self, uploader: S3Uploader, media_repo: MediaRepository, profile_repo: ProfileRepository):
        self.uploader = uploader
        self.media_repo = media_repo
        self.profile_repo = profile_repo

    async def upload_file(self, user_id: int, file_bytes: bytes, filename: str, type: MediaType):
        profile_id = await self.profile_repo.get_profile_id_by_user_id(user_id)
        byte_stream = BytesIO(file_bytes)
        key = await self.uploader.upload_file(byte_stream, filename, str(user_id))
        await self.media_repo.save_media(profile_id, key, type.value)

    async def generate_presigned_urls(self, user_id: int) -> GetPresignedUrlsResponse:
        profile_id = await self.profile_repo.get_profile_id_by_user_id(user_id)
        media_records = await self.media_repo.get_media_by_profile_id(profile_id)
        media_type_map = {record["s3_key"]: record["type"] for record in media_records}

        keys_with_urls = self.uploader.generate_presigned_urls_for_folder(str(user_id))

        presigned_media = []
        for s3_key, url in keys_with_urls:
            media_type = media_type_map.get(s3_key)
            presigned_media.append(PresignedMedia(url=url, type=MediaType(media_type)))
        
        return GetPresignedUrlsResponse(presigned_media=presigned_media)

    async def delete_files(self, user_id: int):
        profile_id = await self.profile_repo.get_profile_id_by_user_id(user_id)
        await self.uploader.delete_folder(str(user_id))
        await self.media_repo.delete_media_by_profile_id(profile_id)
