from database.ProfileRepository import ProfileRepository
from cache.RecommendationCache import RecommendationCache
from kafka_events.producer import KafkaEventProducer
from core.config import get_settings

settings = get_settings()

async def on_geo_resolve_event(
    repo: ProfileRepository, 
    cache: RecommendationCache, 
    producer: KafkaEventProducer,
    event: dict
):
    try:
        user_id = event["user_id"]
        status = event["status"]

        if status == "failed":
            await producer.send_event(settings.KAFKA_GEO_NOTIFICATIONS_TOPIC, {
                'user_id': user_id,
                'status': 'failed'
            })
            return

        latitude = event["latitude"]
        longitude = event["longitude"]

        await repo.update_coordinates(user_id, latitude, longitude)
        await cache.clear(user_id)
        await producer.send_event(settings.KAFKA_GEO_NOTIFICATIONS_TOPIC, {
            'user_id': user_id,
            'status': 'success'
        })
    except Exception:
        await producer.send_event(settings.KAFKA_GEO_NOTIFICATIONS_TOPIC, {
            'user_id': user_id,
            'status': 'failed'
        })
