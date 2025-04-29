from core.celery_app import celery_app
from core.config import get_settings
from services.geo.LocationResolver import LocationResolver
from services.geo.CachedLocationResolver import CachedLocationResolver
from cache.CityCoordinatesCache import CityCoordinatesCache
from kafka_events.producer_sync import KafkaEventProducerSync

settings = get_settings()

@celery_app.task(name="update_user_location")
def update_user_location(user_id: int, city: str):
    producer = KafkaEventProducerSync(settings.kafka_bootstrap_servers)

    producer.start()
    
    resolver = CachedLocationResolver(
        resolver=LocationResolver(), 
        cache=CityCoordinatesCache(redis_url=settings.redis_url_celery)
    )

    coords = resolver.resolve(city)
    
    if coords:
        latitiude, longitude = coords
        producer.send_event(settings.KAFKA_GEO_TOPIC, {
            'user_id': user_id,
            'status': 'success',
            'latitude': latitiude,
            'longitude': longitude
        })
        return
    
    producer.send_event(settings.KAFKA_GEO_TOPIC, {
        'user_id': user_id,
        'status': 'failed',
    })
