import json
from redis.asyncio import Redis
from typing import Optional, Tuple

class CityCoordinatesCache:
    def __init__(self, redis: Redis, ttl: int = 60 * 60 * 24 * 30):
        self.redis = redis
        self.ttl = ttl

    def _key(self, city: str) -> str:
        return f"city_coords:{city.lower()}"

    async def get(self, city: str) -> Optional[Tuple[float, float]]:
        key = self._key(city)
        data = await self.redis.get(key)
        if data:
            try:
                coords = json.loads(data)
                return float(coords["lat"]), float(coords["lon"])
            except (KeyError, ValueError, json.JSONDecodeError):
                return None
        return None

    async def set(self, city: str, latitude: float, longitude: float):
        key = self._key(city)
        value = json.dumps({"lat": latitude, "lon": longitude})
        await self.redis.set(key, value, ex=self.ttl)

    async def clear(self, city: str):
        await self.redis.delete(self._key(city))
