from typing import Optional, Tuple

from cache.CityCoordinatesCache import CityCoordinatesCache
from services.geo.LocationResolver import LocationResolver

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
