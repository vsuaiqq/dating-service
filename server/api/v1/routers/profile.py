from fastapi import APIRouter, Request, Depends, UploadFile, File
from dependency_injector.wiring import inject, Provide
from slowapi import Limiter

from api.v1.dependecies.headers import get_user_id_from_headers
from api.v1.schemas.profile import (
    SaveProfileRequest,
    UpdateFieldRequest,
    ToggleActiveRequest,
    GetProfileResponse,
    SaveProfileResponse,
)
from domain.profile.services.profile_service import ProfileService
from di.container import Container
from shared.exceptions.exceptions import NotFoundException
from core.limiter import user_id_rate_key
from core.logger import logger

router = APIRouter()

limiter = Limiter(
    key_func=user_id_rate_key,
    storage_uri=Container.config().redis_url_limiter
)

@router.put(
    "",
    summary="Сохранить профиль",
    description="Создаёт или обновляет профиль пользователя с переданными данными.",
    tags=["Профиль"],
    response_model=SaveProfileResponse
)
@inject
@limiter.limit("5/minute")
async def save_profile(
    request: Request,
    data: SaveProfileRequest,
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(Provide[Container.services.provided.profile])
):
    logger.info(f"Сохранение профиля для пользователя {user_id}")
    result = await profile_service.save_profile(user_id, data)
    logger.info(f"Профиль успешно сохранён для пользователя {user_id}")
    return result

@router.get(
    "",
    summary="Получить профиль",
    description="Возвращает профиль пользователя по ID из заголовков.",
    tags=["Профиль"],
    response_model=GetProfileResponse
)
@inject
@limiter.limit("5/minute")
async def get_profile_by_user_id(
    request: Request,
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(Provide[Container.services.provided.profile])
):
    logger.info(f"Получение профиля пользователя {user_id}")
    result = await profile_service.get_profile_by_user_id(user_id)
    if result is None:
        logger.warning(f"Профиль не найден для пользователя {user_id}")
        raise NotFoundException()
    logger.info(f"Профиль успешно получен для пользователя {user_id}")
    return result

@router.patch(
    "",
    summary="Обновить поле профиля",
    description="Обновляет указанное поле в профиле пользователя (например, имя или возраст).",
    tags=["Профиль"]
)
@inject
@limiter.limit("10/minute")
async def update_field(
    request: Request,
    data: UpdateFieldRequest,
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(Provide[Container.services.provided.profile])
):
    logger.info(f"Обновление поля {data.field_name} для пользователя {user_id}")
    await profile_service.update_field(user_id, data)
    logger.info(f"Поле {data.field_name} успешно обновлено для пользователя {user_id}")

@router.patch(
    "/active",
    summary="Активировать/деактивировать профиль",
    description="Устанавливает активный/неактивный статус профиля пользователя.",
    tags=["Профиль"]
)
@inject
@limiter.limit("10/minute")
async def toggle_active(
    request: Request,
    data: ToggleActiveRequest,
    user_id: int = Depends(get_user_id_from_headers),
    profile_service: ProfileService = Depends(Provide[Container.services.provided.profile])
):
    logger.info(f"Смена статуса активности профиля на {data.is_active} для пользователя {user_id}")
    await profile_service.toggle_active(user_id, data)
    logger.info(f"Статус активности успешно изменён на {data.is_active} для пользователя {user_id}")

@router.post(
    "/verify-video",
    summary="Верификация по видео",
    description="Принимает видеофайл пользователя и запускает процесс верификации личности.",
    tags=["Профиль"]
)
@inject
@limiter.limit("3/minute")
async def verify_video(
    request: Request,
    user_id: int = Depends(get_user_id_from_headers),
    file: UploadFile = File(..., description="Видеофайл для верификации"),
    profile_service: ProfileService = Depends(Provide[Container.services.provided.profile])
):
    logger.info(f"Начало видео-верификации для пользователя {user_id}")
    profile_service.verify_video(user_id, await file.read())
    logger.info(f"Видео-верификация завершена для пользователя {user_id}")
