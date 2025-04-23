from typing import Optional, Tuple

from geo.CityCoordinatesCache import CityCoordinatesCache
from geo.LocationResolver import LocationResolver

class CachedLocationResolver:
    def __init__(self, resolver: LocationResolver, cache: CityCoordinatesCache):
        self.resolver = resolver
        self.cache = cache

    async def resolve(self, city: str) -> Optional[Tuple[float, float]]:
        cached = await self.cache.get(city)
        if cached:
            return cached

        coords = await self.resolver.resolve_coordinates(city)
        if coords:
            await self.cache.set(city, *coords)
        return coords
