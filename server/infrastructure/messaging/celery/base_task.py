from celery import Task
from core.config import get_settings
from services.location.location_resolver import LocationResolver
from services.location.cached_location_resolver import CachedLocationResolver
from infrastructure.messaging.kafka.producer_sync import KafkaEventProducerSync
from infrastructure.cache.redis.city_coordinates_cache import CityCoordinatesCache

settings = get_settings()

class BaseTask(Task):
    abstract = True
    _producer = None
    _location_resolver = None

    @property
    def producer(self):
        if self._producer is None:
            self._producer = KafkaEventProducerSync(settings.kafka_bootstrap_servers)
            self._producer.start()
        return self._producer

    @property
    def location_resolver(self):
        if self._location_resolver is None:
            self._location_resolver = CachedLocationResolver(
                resolver=LocationResolver(),
                cache=CityCoordinatesCache(redis_url=settings.redis_url_cache)
            )
        return self._location_resolver

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        if self._producer:
            self._producer.stop()
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def __del__(self):
        if self._producer:
            self._producer.stop()