from database.ProfileRepository import ProfileRepository
from cache.RecommendationCache import RecommendationCache
from kafka_events.producer import KafkaEventProducer
from core.config import get_settings
from models.kafka.events import LocationResolveResultEvent

settings = get_settings()

async def on_geo_resolve_event(
    repo: ProfileRepository, 
    cache: RecommendationCache, 
    producer: KafkaEventProducer,
    event: LocationResolveResultEvent
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
