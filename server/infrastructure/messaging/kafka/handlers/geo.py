from core.config import Settings
from domain.profile.repositories.profile_repository import ProfileRepository
from infrastructure.messaging.kafka.producer import KafkaEventProducer
from infrastructure.cache.redis.recommendation_cache import RecommendationCache
from contracts.kafka.events import LocationResolveResultEvent

async def on_geo_resolve_event(
    event: LocationResolveResultEvent,
    repo: ProfileRepository, 
    cache: RecommendationCache, 
    producer: KafkaEventProducer,
    settings: Settings
):
    user_id = event.user_id
    status = event.status

    if status == "success":
        latitude = event.latitude
        longitude = event.longitude

        await repo.update_profile_field(user_id, 'latitude', latitude)
        await repo.update_profile_field(user_id, 'longitude', longitude)

        await cache.clear(user_id)

        event = LocationResolveResultEvent(
            user_id=user_id,
            status='success'
        )
    
    await producer.send_event(settings.KAFKA_GEO_NOTIFICATIONS_TOPIC, event.model_dump())
