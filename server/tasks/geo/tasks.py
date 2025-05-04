from core.celery_app import celery_app
from core.config import get_settings
from geo.LocationResolver import LocationResolver
from geo.CachedLocationResolver import CachedLocationResolver
from cache.CityCoordinatesCache import CityCoordinatesCache
from kafka_events.producer_sync import KafkaEventProducerSync
from models.kafka.events import LocationResolveResultEvent

settings = get_settings()

@celery_app.task(name="update_user_location")
def update_user_location(user_id: int, city: str):
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
            user_id=user_id,
            status='success',
            latitude=latitude,
            longitude=longitude
        )
    else:
        event = LocationResolveResultEvent(
            user_id=user_id,
            status='failed'
        )

    producer.send_event(settings.KAFKA_GEO_TOPIC, event.model_dump())

    producer.stop()
