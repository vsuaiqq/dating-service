from fastapi import Request, Header

from services.profile.ProfileService import ProfileService
from services.recsys.RecommendationsService import RecommendationsService
from services.media.MediaService import MediaService
from services.swipe.SwipeService import SwipeService

def get_profile_service(request: Request) -> ProfileService:
    return request.app.state.profile_service

def get_recommendations_service(request: Request) -> RecommendationsService:
    return request.app.state.recommendations_service

def get_media_service(request: Request) -> MediaService:
    return request.app.state.media_service

def get_swipe_service(request: Request) -> SwipeService:
    return request.app.state.swipe_service

async def get_user_id_from_headers(x_user_id: int = Header(..., alias="X-User-ID")):
    return x_user_id

async def get_username_from_headers(x_telegram_username: str = Header(..., alias="X-Telegram-Username")):
    return x_telegram_username
