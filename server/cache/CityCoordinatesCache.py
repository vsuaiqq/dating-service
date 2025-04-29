import json
import redis
from typing import Optional, Tuple

class CityCoordinatesCache:
    def __init__(self, redis_url: str, ttl: int = 60 * 60 * 24 * 30):
        self.redis = redis.StrictRedis.from_url(redis_url, decode_responses=True)
        self.ttl = ttl

    def _key(self, city: str) -> str:
        return f"city_coords:{city.lower()}"

    def get(self, city: str) -> Optional[Tuple[float, float]]:
        key = self._key(city)
        data = self.redis.get(key)
        if data:
            try:
                coords = json.loads(data)
                return float(coords["lat"]), float(coords["lon"])
            except (KeyError, ValueError, json.JSONDecodeError):
                return None
        return None

    def set(self, city: str, latitude: float, longitude: float):
        key = self._key(city)
        value = json.dumps({"lat": latitude, "lon": longitude})
        self.redis.setex(key, self.ttl, value)

    def clear(self, city: str):
        self.redis.delete(self._key(city))
