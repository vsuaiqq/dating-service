from fastapi import APIRouter, Depends, HTTPException
from core.dependecies import get_swipe_service, get_username_from_headers
from services.swipe.SwipeService import SwipeService
from models.api.swipe.requests import AddSwipeRequest
from core.logger import logger
import datetime

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

        return {
            "status": "success",
            "action": swipe.action.value,
            "from_user": username,
            "to_user_id": swipe.to_user_id,
            "timestamp": datetime.utcnow().isoformat()
        }

    except ValueError as e:
        logger.warning(
            "Swipe validation failed",
            extra={
                "event": "swipe_validation_error",
                "from_user": username,
                "error": str(e),
                "swipe_data": {
                    "to_user_id": swipe.to_user_id,
                    "action": swipe.action.value,
                    "message_length": len(swipe.message) if swipe.message else 0
                }
            }
        )
        raise HTTPException(
            status_code=400,
            detail={"error": str(e), "code": "validation_error"}
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