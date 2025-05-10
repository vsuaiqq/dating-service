from fastapi import APIRouter, Request, Depends, UploadFile, File, Form
from dependency_injector.wiring import inject, Provide
from slowapi import Limiter

from api.v1.dependecies.headers import get_user_id_from_headers
from api.v1.schemas.media import MediaType, GetPresignedUrlsResponse
from domain.media.services.media_service import MediaService
from di.container import Container
from core.limiter import user_id_rate_key
from core.logger import logger

router = APIRouter()
limiter = Limiter(
    key_func=user_id_rate_key,
    storage_uri=Container.config().redis_url_limiter
)

@router.post(
    "/upload",
    summary="Загрузка файла",
    description="Загружает медиафайл пользователя на сервер. Тип файла передаётся через форму.",
    tags=["Медиа"]
)
@inject
@limiter.limit("5/minute")
async def upload_file(
    request: Request,
    user_id: int = Depends(get_user_id_from_headers),
    file: UploadFile = File(..., description="Файл для загрузки"),
    type: MediaType = Form(..., description="Тип медиафайла"),
    media_service: MediaService = Depends(Provide[Container.services.provided.media])
):
    logger.info(f"Начало загрузки файла: {file.filename}")
    await media_service.upload_file(user_id, await file.read(), file.filename, type)
    logger.info(f"Файл успешно загружен: {file.filename}")


@router.get(
    "/presigned-urls",
    summary="Получение подписанных URL-адресов",
    description="Возвращает список подписанных URL-адресов для загрузки медиафайлов.",
    tags=["Медиа"],
    response_model=GetPresignedUrlsResponse
)
@inject
@limiter.limit("10/minute")
async def get_presigned_urls(
    request: Request,
    user_id: int = Depends(get_user_id_from_headers),
    media_service: MediaService = Depends(Provide[Container.services.provided.media])
):
    logger.info(f"Генерация подписанных URL для пользователя: {user_id}")
    result = await media_service.generate_presigned_urls(user_id)
    logger.info(f"Подписанные URL сгенерированы для пользователя: {user_id}")
    return result


@router.delete(
    "/files",
    summary="Удаление файлов",
    description="Удаляет все файлы пользователя с сервера.",
    tags=["Медиа"]
)
@inject
@limiter.limit("3/minute")
async def delete_files(
    request: Request,
    user_id: int = Depends(get_user_id_from_headers),
    media_service: MediaService = Depends(Provide[Container.services.provided.media])
):
    logger.info(f"Удаление файлов пользователя: {user_id}")
    await media_service.delete_files(user_id)
    logger.info(f"Файлы успешно удалены для пользователя: {user_id}")
