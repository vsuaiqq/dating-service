from typing import Optional, Tuple

from infrastructure.cache.redis.city_coordinates_cache import CityCoordinatesCache
from location.resolver import LocationResolver

class CachedLocationResolver:
    def __init__(self, resolver: LocationResolver, cache: CityCoordinatesCache):
        self.resolver = resolver
        self.cache = cache

    def resolve(self, city: str) -> Optional[Tuple[float, float]]:
        cached = self.cache.get(city)
        if cached:
            return cached

        coords = self.resolver.resolve_coordinates(city)
        if coords:
            self.cache.set(city, *coords)
        return coords
