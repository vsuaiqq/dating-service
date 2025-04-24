from redis.asyncio import Redis
from typing import List, Optional

class RecommendationCache:
    def __init__(self, redis: Redis, ttl: int = 60 * 60):
        self.redis = redis
        self.ttl = ttl

    def _key(self, user_id: int) -> str:
        return f"recs:{user_id}"

    async def get(self, user_id: int) -> List[int]:
        key = self._key(user_id)
        data = await self.redis.lrange(key, 0, -1)
        return [int(x) for x in data]

    async def set(self, user_id: int, recs: List[int]):
        key = self._key(user_id)
        if not recs:
            return

        pipe = self.redis.pipeline()
        for rec_id in recs:
            pipe.rpush(key, rec_id)
        pipe.expire(key, self.ttl)
        await pipe.execute()

    async def pop_next(self, user_id: int) -> Optional[int]:
        key = self._key(user_id)
        value = await self.redis.lpop(key)
        return int(value) if value else None

    async def clear(self, user_id: int):
        await self.redis.delete(self._key(user_id))
