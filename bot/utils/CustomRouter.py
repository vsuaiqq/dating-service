from aiogram import Router
from typing import Optional
from api.ProfileClient import ProfileClient
from api.MediaClient import MediaClient
from api.RecSysClient import RecSysClient
from api.SwipeClient import SwipeClient

class CustomRouter(Router):
    profile_client: Optional[ProfileClient] = None
    media_client: Optional[MediaClient] = None
    recsys_client: Optional[RecSysClient] = None
    swipe_client: Optional[SwipeClient] = None
