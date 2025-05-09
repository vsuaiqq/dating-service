import boto3
import uuid
import mimetypes
from typing import BinaryIO, Optional, List
from botocore.exceptions import BotoCoreError, ClientError

class S3Uploader:
    def __init__(self, client: boto3.client, bucket_name: str, public: bool = False):
        self.client = client
        self.bucket_name = bucket_name
        self.public = public

    def _generate_key(self, original_filename: str, folder: Optional[str] = None) -> str:
        extension = original_filename.split(".")[-1] if "." in original_filename else ""
        filename = f"{uuid.uuid4().hex}.{extension}" if extension else uuid.uuid4().hex
        return f"{folder.rstrip('/')}/{filename}" if folder else filename

    def _guess_content_type(self, filename: str) -> str:
        content_type, _ = mimetypes.guess_type(filename)
        if not content_type:
            if filename.lower().endswith(('.jpg', '.jpeg')):
                return 'image/jpeg'
            elif filename.lower().endswith('.mp4'):
                return 'video/mp4'
        return content_type or "application/octet-stream"

    def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        try:
            return self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
        except (BotoCoreError, ClientError) as e:
            raise RuntimeError(f"Ошибка генерации pre-signed URL для файла {key}: {e}")

    def generate_presigned_urls_for_folder(self, folder: str, expiration: int = 3600) -> List[str]:
        try:
            response = self.client.list_objects_v2(Bucket=self.bucket_name, Prefix=folder.rstrip('/') + '/')
            if 'Contents' not in response:
                return []

            keys_with_urls = []
            for obj in response['Contents']:
                key = obj['Key']
                keys_with_urls.append((key, self.generate_presigned_url(key, expiration)))
            return keys_with_urls
        except (BotoCoreError, ClientError) as e:
            raise RuntimeError(f"Ошибка получения URL-ов для папки {folder}: {e}")

    async def upload_file(self, file: BinaryIO, original_filename: str, folder: Optional[str] = None) -> str:
        key = self._generate_key(original_filename, folder)
        file.seek(0)

        content_type = self._guess_content_type(original_filename)
        extra_args = {"ContentType": content_type}
        if self.public:
            extra_args["ACL"] = "public-read"

        try:
            self.client.upload_fileobj(file, self.bucket_name, key, ExtraArgs=extra_args)
            return key
        except (BotoCoreError, ClientError) as e:
            raise RuntimeError(f"Ошибка загрузки файла '{original_filename}' в S3: {e}")

    async def delete_file_by_key(self, key: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
        except (BotoCoreError, ClientError) as e:
            raise RuntimeError(f"Ошибка удаления файла с ключом {key} из S3: {e}")

    async def delete_folder(self, folder: str) -> None:
        try:
            response = self.client.list_objects_v2(Bucket=self.bucket_name, Prefix=folder.rstrip('/') + '/')
            if 'Contents' in response:
                objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
                self.client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': objects_to_delete}
                )
        except (BotoCoreError, ClientError) as e:
            raise RuntimeError(f"Ошибка удаления папки {folder} из S3: {e}")
