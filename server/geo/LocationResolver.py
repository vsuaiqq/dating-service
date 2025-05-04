import time
from geopy.geocoders import Nominatim
from geopy.exc import GeopyError
from geopy.extra.rate_limiter import RateLimiter
from typing import Optional, Tuple

class LocationResolver:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="dating-service")
        self.geocode = RateLimiter(
            self.geolocator.geocode,
            min_delay_seconds=2,
            max_retries=5,
            swallow_exceptions=False
        )

    def resolve_coordinates(self, city: str) -> Optional[Tuple[float, float]]:
        for _ in range(5):
            time.sleep(2)
            try:
                location = self.geocode(city)
                if location:
                    return location.latitude, location.longitude
            except GeopyError:
                pass
        return None
