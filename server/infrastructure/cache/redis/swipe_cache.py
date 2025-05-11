from typing import Set
from redis.asyncio import Redis

def get_swipes_key(user_id: int) -> str:
        return f"swipes:{user_id}"

class SwipeCache:
    def __init__(self, redis: Redis, ttl: int = 60 * 60 * 24 * 3):
        self.redis = redis
        self.ttl = ttl

    async def set(self, from_user_id: int, to_user_id: int):
        key = get_swipes_key(from_user_id)
        await self.redis.sadd(key, to_user_id)
        await self.redis.expire(key, self.ttl)

    async def get(self, user_id: int) -> Set[int]:
        key = get_swipes_key(user_id)
        ids = await self.redis.smembers(key)
        return set(map(int, ids))

    async def clear(self, user_id: int):
        await self.redis.delete(get_swipes_key(user_id))
    
    async def close(self):
        await self.redis.close()
