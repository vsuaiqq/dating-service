from fastapi import APIRouter, Depends, HTTPException

from core.dependecies import get_swipe_service, get_username_from_headers
from core.logger import logger
from services.swipe.SwipeService import SwipeService
from models.api.swipe.requests import AddSwipeRequest

router = APIRouter()

@router.post("")
async def add_swipe(
    swipe: AddSwipeRequest,
    username: str = Depends(get_username_from_headers),
    swipe_service: SwipeService = Depends(get_swipe_service)
):
    try:
        logger.info(
            "Starting swipe processing",
            extra={
                "event": "swipe_initiated",
                "from_user": username,
                "to_user_id": swipe.to_user_id,
                "action_type": swipe.action.value,
                "has_message": swipe.message is not None
            }
        )

        result = await swipe_service.add_swipe(username, swipe)

        logger.info(
            "Swipe processed successfully",
            extra={
                "event": "swipe_processed",
                "from_user": username,
                "to_user_id": swipe.to_user_id,
                "action_type": swipe.action.value,
                "processing_result": result
            }
        )
    except Exception as e:
        logger.error(
            "Swipe processing failed",
            exc_info=True,
            extra={
                "event": "swipe_processing_error",
                "from_user": username,
                "to_user_id": swipe.to_user_id,
                "action_type": swipe.action.value,
                "error_type": type(e).__name__,
                "error_details": str(e)
            }
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "code": "server_error"
            }
        )
