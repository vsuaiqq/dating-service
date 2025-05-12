from fastapi import APIRouter, Request, Depends, status
from dependency_injector.wiring import inject, Provide
from slowapi import Limiter

from api.v1.deps.headers import get_username_from_headers
from api.v1.schemas.swipe import AddSwipeRequest
from domain.swipe.services.swipe_service import SwipeService
from di.container import Container
from core.limiter import get_user_id_rate_key
from core.logger import logger

router = APIRouter()

limiter = Limiter(
    key_func=get_user_id_rate_key,
    storage_uri=Container.config().redis_url_limiter
)


@router.post(
    "",
    tags=["Swipe"],
    summary="Add swipe action",
    description="Add a like, dislike, or question swipe toward another user.",
    responses={
        200: {"description": "Swipe processed"},
        429: {"description": "Rate limit exceeded"},
    },
)
@inject
@limiter.limit("30/minute")
async def add_swipe(
    request: Request,
    swipe: AddSwipeRequest,
    username: str = Depends(get_username_from_headers),
    swipe_service: SwipeService = Depends(Provide[Container.services.provided.swipe]),
):
    logger.info(
        "Swipe processing started",
        extra={
            "event": "swipe_initiated",
            "from_user": username,
            "to_user_id": swipe.to_user_id,
            "action_type": swipe.action.value,
            "has_message": swipe.message is not None,
        },
    )

    result = await swipe_service.add_swipe(username, swipe)

    logger.info(
        "Swipe processed successfully",
        extra={
            "event": "swipe_processed",
            "from_user": username,
            "to_user_id": swipe.to_user_id,
            "action_type": swipe.action.value,
            "processing_result": result,
        },
    )

    return result
