from fastapi import APIRouter, Depends, HTTPException

from core.dependecies import get_swipe_service
from services.swipe.SwipeService import SwipeService
from models.swipe.requests import AddSwipeRequest

router = APIRouter()

@router.post("")
async def add_swipe(
    swipe: AddSwipeRequest,
    swipe_service: SwipeService = Depends(get_swipe_service)
):
    try:
        await swipe_service.add_swipe(swipe)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
