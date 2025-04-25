import asyncio
from geopy.geocoders import Nominatim
from typing import Optional, Tuple
from geopy.extra.rate_limiter import RateLimiter
from asyncio.exceptions import TimeoutError

class LocationResolver:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="dating-service")
        self.geocode = RateLimiter(
            self.geolocator.geocode,
            min_delay_seconds=2,
            max_retries=5,
            swallow_exceptions=False
        )
        self.semaphore = asyncio.Semaphore(10)

    async def resolve_coordinates(self, city: str) -> Optional[Tuple[float, float]]:
        async with self.semaphore:
            for _ in range(5):
                try:
                    location = await asyncio.wait_for(
                        asyncio.to_thread(self.geocode, city),
                        timeout=5
                    )
                    if location:
                        return location.latitude, location.longitude
                except (TimeoutError, Exception):
                    await asyncio.sleep(1)
            return None
