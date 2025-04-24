import asyncio
from geopy.geocoders import Nominatim
from typing import Optional, Tuple
from geopy.extra.rate_limiter import RateLimiter

class LocationResolver:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="dating-service")
        self.geocode = RateLimiter(self.geolocator.geocode, min_delay_seconds=2, max_retries=5)
        self.semaphore = asyncio.Semaphore(10)

    async def resolve_coordinates(self, city: str) -> Optional[Tuple[float, float]]:
        async with self.semaphore:
            retries = 50
            for attempt in range(retries):
                try:
                    location = await asyncio.to_thread(self.geocode, city)
                    if location:
                        return location.latitude, location.longitude
                except Exception as e:
                    pass
            return None
