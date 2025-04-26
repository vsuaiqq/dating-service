from geo.CachedLocationResolver import CachedLocationResolver
from database.ProfileRepository import ProfileRepository
from cache.RecommendationCache import RecommendationCache
from kafka_events.producer import KafkaEventProducer
from config import KAFKA_GEO_NOTIFICATIONS_TOPIC
import asyncio

async def handle_geo_request(
        repo: ProfileRepository,
        resolver: CachedLocationResolver,
        cache: RecommendationCache,
        producer: KafkaEventProducer,
        event: dict
):
    user_id = event.get("user_id")
    city = event.get("city")

    if not user_id or not city:
        return

    try:
        for attempt in range(3):
            try:
                coords = await resolver.resolve(city)
                if coords:
                    latitude, longitude = coords
                    await repo.update_coordinates(user_id, latitude, longitude)
                    await cache.clear(user_id)

                    await producer.send_event(KAFKA_GEO_NOTIFICATIONS_TOPIC, {
                        'user_id': user_id,
                        'status': 'success',
                        'city': city,
                        'latitude': latitude,
                        'longitude': longitude,
                        'attempt': attempt + 1
                    })
                    return

                await asyncio.sleep(1)

            except Exception as e:
                if attempt == 2:
                    raise

        await producer.send_event(KAFKA_GEO_NOTIFICATIONS_TOPIC, {
            'user_id': user_id,
            'status': 'failed',
            'reason': 'coordinates_not_found',
            'city': city
        })

    except Exception as e:
        await producer.send_event(KAFKA_GEO_NOTIFICATIONS_TOPIC, {
            'user_id': user_id,
            'status': 'failed',
            'reason': 'internal_error',
            'error': str(e)
        })