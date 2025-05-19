from infrastructure.messaging.celery.base_task import KafkaTask
from services.location.location_resolver import LocationResolver
from services.location.cached_location_resolver import CachedLocationResolver
from infrastructure.cache.redis.city_coordinates_cache import CityCoordinatesCache
from core.config import get_settings

settings = get_settings()

class LocationTask(KafkaTask):
    abstract = True

    _location_resolver: CachedLocationResolver = None

    @property
    def location_resolver(self) -> CachedLocationResolver:
        if self._location_resolver is None:
            self._location_resolver = CachedLocationResolver(
                resolver=LocationResolver(),
                cache=CityCoordinatesCache(redis_url=settings.redis_url_cache)
            )
        return self._location_resolver
