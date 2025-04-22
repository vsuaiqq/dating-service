from aiogram import Router
from typing import Optional
from api.ProfileClient import ProfileClient
from api.S3Client import S3Client
from api.RecSysClient import RecSysClient
from api.SwipeClient import SwipeClient
from services.RecommendationCache import RecommendationCache

class CustomRouter(Router):
    profile_client: Optional[ProfileClient] = None
    s3_client: Optional[S3Client] = None
    recsys_client: Optional[RecSysClient] = None
    swipe_client: Optional[SwipeClient] = None
    recommendation_cache: Optional[RecommendationCache] = None
