import asyncpg
from typing import List

class MediaRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def save_media(self, user_id: int, s3_key: str, media_type: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO media (user_id, type, s3_key)
                VALUES ($1, $2, $3)
            """, user_id, media_type, s3_key)

    async def get_media_by_user_id(self, user_id: int) -> List[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT type, s3_key FROM media WHERE user_id = $1
            """, user_id)
            return rows
    
    async def delete_media_by_user_id(self, user_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM media WHERE user_id = $1
            """, user_id)
