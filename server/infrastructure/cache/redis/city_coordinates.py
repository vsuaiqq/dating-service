import json
import redis
from typing import Optional, Tuple

from infrastructure.cache.redis.keys import get_city_coords_key

class CityCoordinatesCache:
    def __init__(self, redis_url: str, ttl: int = 60 * 60 * 24 * 30):
        self.redis = redis.StrictRedis.from_url(redis_url, decode_responses=True)
        self.ttl = ttl

    def get(self, city: str) -> Optional[Tuple[float, float]]:
        key = get_city_coords_key(city)
        data = self.redis.get(key)
        if data:
            try:
                coords = json.loads(data)
                return float(coords["lat"]), float(coords["lon"])
            except (KeyError, ValueError, json.JSONDecodeError):
                return None
        return None

    def set(self, city: str, latitude: float, longitude: float):
        key = get_city_coords_key(city)
        value = json.dumps({"lat": latitude, "lon": longitude})
        self.redis.setex(key, self.ttl, value)

    def clear(self, city: str):
        self.redis.delete(get_city_coords_key(city))
    
    def close(self):
        self.redis.close()
