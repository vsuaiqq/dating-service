from services.geo.CachedLocationResolver import CachedLocationResolver
from database.ProfileRepository import ProfileRepository
from cache.RecommendationCache import RecommendationCache
from kafka_events.producer import KafkaEventProducer
from core.config import KAFKA_GEO_NOTIFICATIONS_TOPIC

async def handle_geo_request(
    repo: ProfileRepository, 
    resolver: CachedLocationResolver, 
    cache: RecommendationCache, 
    producer: KafkaEventProducer,
    event: dict
):
    user_id = event["user_id"]
    city = event["city"]

    try:
        coords = await resolver.resolve(city)
        if coords:
            latitude, longitude = coords
            await repo.update_coordinates(user_id, latitude, longitude)
            await cache.clear(user_id)
            await producer.send_event(KAFKA_GEO_NOTIFICATIONS_TOPIC, {
                'user_id': user_id,
                'status': 'success'
            })
        else:
            await producer.send_event(KAFKA_GEO_NOTIFICATIONS_TOPIC, {
                'user_id': user_id,
                'status': 'failed'
            })
    except Exception as e:
        await producer.send_event(KAFKA_GEO_NOTIFICATIONS_TOPIC, {
            'user_id': user_id,
            'status': 'failed'
        })
