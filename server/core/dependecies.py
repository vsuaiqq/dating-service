from fastapi import Request

from services.profile.ProfileService import ProfileService
from services.recsys.RecommendationsService import RecommendationsService
from services.s3.S3Service import S3Service
from services.swipe.SwipeService import SwipeService

def get_profile_service(request: Request) -> ProfileService:
    return request.app.state.profile_service

def get_recommendations_service(request: Request) -> RecommendationsService:
    return request.app.state.recommendations_service

def get_s3_service(request: Request) -> S3Service:
    return request.app.state.s3_service

def get_swipe_service(request: Request) -> SwipeService:
    return request.app.state.swipe_service
