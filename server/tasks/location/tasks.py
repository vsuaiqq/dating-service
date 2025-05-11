from core.config import get_settings
from services.location.location_resolver import LocationResolver
from services.location.cached_location_resolver import CachedLocationResolver
from infrastructure.messaging.celery.celery_app import celery_app
from infrastructure.messaging.kafka.producer_sync import KafkaEventProducerSync
from infrastructure.cache.redis.city_coordinates_cache import CityCoordinatesCache
from contracts.kafka.events import LocationResolveResultEvent

settings = get_settings()

@celery_app.task(name="location.update_user_location", bind=True)
def update_user_location(self, user_id: int, city: str):
    try:
        producer = KafkaEventProducerSync(settings.kafka_bootstrap_servers)
        producer.start()

        resolver = CachedLocationResolver(
            resolver=LocationResolver(),
            cache=CityCoordinatesCache(redis_url=settings.redis_url_cache)
        )

        coords = resolver.resolve(city)

        if coords:
            latitude, longitude = coords
            event = LocationResolveResultEvent(
                user_id=user_id, status="success",
                latitude=latitude, longitude=longitude
            )
        else:
            event = LocationResolveResultEvent(user_id=user_id, status="failed")

        producer.send_event(settings.KAFKA_GEO_TOPIC, event.model_dump())
        producer.stop()
    except Exception as exc:
        raise self.retry(exc=exc)
