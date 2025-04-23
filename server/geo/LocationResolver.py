import asyncio
from geopy.geocoders import Nominatim
from typing import Optional, Tuple
from geopy.extra.rate_limiter import RateLimiter

class LocationResolver:
    def __init__(self):
        self.geolocator = Nominatim(
            user_agent="dating-service"
        )

        self.geocode = RateLimiter(
            self.geolocator.geocode,
            min_delay_seconds=1,
            max_retries=5
        )

    async def resolve_coordinates(self, city: str) -> Optional[Tuple[float, float]]:
        try:
            location = await asyncio.to_thread(self.geocode, city)
            if location:
                return location.latitude, location.longitude
            return None
        except Exception as e:
            print(f"Geocoding error for {city}: {str(e)}")
            return None
