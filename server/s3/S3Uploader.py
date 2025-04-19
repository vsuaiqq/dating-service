import boto3
import uuid
import mimetypes
from typing import BinaryIO, Optional
from botocore.exceptions import BotoCoreError, ClientError
from botocore.config import Config

class S3Uploader:
    def __init__(
        self,
        bucket_name: str,
        region: str,
        access_key: str,
        secret_key: str,
        endpoint_url: Optional[str] = None,
        public: bool = False,
        s3_client_config: Optional[dict] = None,
    ):
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url.rstrip("/") if endpoint_url else None
        self.public = public

        self.s3 = boto3.client(
            "s3",
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=self.endpoint_url,
            config=Config(connect_timeout=60, read_timeout=60, **(s3_client_config or {}))
        )

    def _generate_key(self, original_filename: str) -> str:
        extension = original_filename.split(".")[-1] if "." in original_filename else ""
        if extension:
            return f"{uuid.uuid4().hex}.{extension}"
        return f"{uuid.uuid4().hex}"

    def _guess_content_type(self, filename: str) -> str:
        content_type, _ = mimetypes.guess_type(filename)
        if not content_type:
            if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
                return 'image/jpeg'
            elif filename.lower().endswith('.mp4'):
                return 'video/mp4'
        return content_type or "application/octet-stream"

    def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        try:
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except (BotoCoreError, ClientError) as e:
            raise RuntimeError(f"Ошибка генерации pre-signed URL для файла {key}: {e}")

    async def upload_file(self, file: BinaryIO, original_filename: str) -> str:
        key = self._generate_key(original_filename)
        file.seek(0)

        content_type = self._guess_content_type(original_filename)

        extra_args = {"ContentType": content_type}
        if self.public:
            extra_args["ACL"] = "public-read"

        try:
            self.s3.upload_fileobj(file, self.bucket_name, key, ExtraArgs=extra_args)
            return key
        except (BotoCoreError, ClientError) as e:
            raise RuntimeError(f"Ошибка загрузки файла '{original_filename}' в S3: {e}")

    async def delete_file_by_key(self, key: str) -> None:
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=key)
        except (BotoCoreError, ClientError) as e:
            raise RuntimeError(f"Ошибка удаления файла с ключом {key} из S3: {e}")

    async def delete_files(self, keys: List[str]) -> None:
        try:
            objects = [{'Key': key} for key in keys]
            self.s3.delete_objects(
                Bucket=self.bucket_name,
                Delete={'Objects': objects}
            )
        except (BotoCoreError, ClientError) as e:
            raise RuntimeError(f"Ошибка массового удаления файлов из S3: {e}")
        
    async def delete_user_data(self, user_id: int):
        photos = await self.get_user_photos(user_id)
        photo_keys = [p['file_id'] for p in photos]
        
        if photo_keys:
            await self.s3_uploader.delete_files(photo_keys)
        
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM user_photos WHERE user_id = $1", user_id)
            await conn.execute("DELETE FROM users WHERE telegram_id = $1", user_id)
            
    async def update_user_photo(self, user_id: int, new_photo: UploadFile):
        file_bytes = await new_photo.read()
        file_io = io.BytesIO(file_bytes)
        
        try:
            key = await self.s3_uploader.upload_file(file_io, new_photo.filename)
            
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO user_photos (user_id, file_id, is_main)
                    VALUES ($1, $2, TRUE)
                    ON CONFLICT (user_id) DO UPDATE
                    SET file_id = EXCLUDED.file_id
                """, user_id, key)
                
            return key
        finally:
            file_io.close()
    async def check_file_exists(self, key: str) -> bool:
        try:
            self.s3.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise

    async def get_file_metadata(self, key: str) -> dict:
        try:
            response = self.s3.head_object(Bucket=self.bucket_name, Key=key)
            return {
                'content_type': response['ContentType'],
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'metadata': response.get('Metadata', {})
            }
        except ClientError as e:
            raise RuntimeError(f"Error getting file metadata: {e}")

    async def copy_file(self, source_key: str, dest_key: str) -> str:
        try:
            self.s3.copy_object(
                Bucket=self.bucket_name,
                CopySource={'Bucket': self.bucket_name, 'Key': source_key},
                Key=dest_key
            )
            return dest_key
        except ClientError as e:
            raise RuntimeError(f"Error copying file: {e}")