from typing import Set
from redis.asyncio import Redis

class SwipeCache:
    def __init__(self, redis: Redis, ttl: int = 60 * 60 * 24 * 3):
        self.redis = redis
        self.ttl = ttl

    def _key(self, user_id: int) -> str:
        return f"swipes:{user_id}"

    async def set(self, from_user_id: int, to_user_id: int):
        key = self._key(from_user_id)
        await self.redis.sadd(key, to_user_id)
        await self.redis.expire(key, self.ttl)

    async def get(self, user_id: int) -> Set[int]:
        key = self._key(user_id)
        ids = await self.redis.smembers(key)
        return set(map(int, ids))

    async def clear(self, user_id: int):
        await self.redis.delete(self._key(user_id))
    
    async def close(self):
        await self.redis.close()
