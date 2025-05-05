from typing import Optional

from database.ProfileRepository import ProfileRepository
from recsys.EmbeddingRecommender import EmbeddingRecommender
from kafka_events.producer import KafkaEventProducer
from cache.RecommendationCache import RecommendationCache
from core.config import Settings
from models.api.profile.requests import SaveProfileRequest, ToggleActiveRequest, UpdateFieldRequest
from models.api.profile.responses import SaveProfileResponse, GetProfileResponse
from tasks.geo.tasks import update_user_location
from tasks.video.tasks import validate_video

class ProfileService:
    def __init__(
        self,
        repo: ProfileRepository,
        producer: KafkaEventProducer,
        recommender: EmbeddingRecommender,
        cache: RecommendationCache,
        settings: Settings,
    ):
        self.repo = repo
        self.producer = producer
        self.recommender = recommender
        self.cache = cache
        self.settings = settings
        self.fallback_coordinates = (55.625578, 37.6063916)

    async def save_profile(self, user_id: int, data: SaveProfileRequest) -> SaveProfileResponse:
        if data.latitude is None or data.longitude is None:
            await self._notify_geo_waiting(user_id)
            update_user_location.delay(user_id=user_id, city=data.city)

        lat = data.latitude or self.fallback_coordinates[0]
        lon = data.longitude or self.fallback_coordinates[1]

        profile_id = await self.repo.save_profile(
            user_id=user_id,
            name=data.name,
            gender=data.gender,
            city=data.city,
            age=data.age,
            interesting_gender=data.interesting_gender,
            about=data.about,
            latitude=lat,
            longitude=lon,
        )

        await self.recommender.update_user_embedding(user_id)

        return SaveProfileResponse(profile_id=profile_id)

    async def update_field(self, user_id: int, data: UpdateFieldRequest):
        if data.field_name != "coordinates":
            await self.repo.update_profile_field(user_id, data.field_name, data.value)
        
        if data.field_name == 'about':
            await self.recommender.update_user_embedding(user_id)
            await self.cache.clear(user_id)

        if data.field_name == 'city':
            await self._notify_geo_waiting(user_id)
            update_user_location.delay(user_id=user_id, city=data.value)

        if data.field_name == 'coordinates':
            await self.repo.update_profile_field(user_id, 'latitude', data.value.latitude)
            await self.repo.update_profile_field(user_id, 'longitude', data.value.longitude)
            await self.repo.reset_city(user_id)
            await self.cache.clear(user_id)

    async def toggle_active(self, user_id: int, data: ToggleActiveRequest):
        await self.repo.toggle_profile_active(user_id, data.is_active)

    async def get_profile_by_user_id(self, user_id: int) -> Optional[GetProfileResponse]:
        row = await self.repo.get_profile_by_user_id(user_id)
        if row:
            return GetProfileResponse(**row)
        return None

    def verify_video(self, user_id: int, file_bytes: bytes):
        validate_video.delay(user_id, file_bytes)

    async def _notify_geo_waiting(self, user_id: int):
        await self.producer.send_event(
            self.settings.KAFKA_GEO_NOTIFICATIONS_TOPIC,
            {"user_id": user_id, "status": "waited"}
        )
