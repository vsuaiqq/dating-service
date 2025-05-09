from redis.asyncio import Redis
from typing import List, Tuple

class RecommendationCache:
    def __init__(self, redis: Redis, ttl: int = 60 * 60):
        self.redis = redis
        self.ttl = ttl

    def _key(self, user_id: int) -> str:
        return f"recs:{user_id}"

    async def get(self, user_id: int) -> List[Tuple[int, float]]:
        key = self._key(user_id)
        results = await self.redis.zrange(key, 0, -1, withscores=True)
        return [(int(member), score) for member, score in results]

    async def set(self, user_id: int, recs: List[Tuple[int, float]]):
        key = self._key(user_id)
        if not recs:
            return
        members = {str(uid): float(score) for uid, score in recs}
        await self.redis.zadd(key, members)
        await self.redis.expire(key, self.ttl)

    async def clear(self, user_id: int):
        await self.redis.delete(self._key(user_id))
    
    async def close(self):
        await self.redis.close()
