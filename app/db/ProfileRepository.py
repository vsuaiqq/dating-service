import asyncpg
from typing import List, Tuple, Optional

class ProfileRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def save_profile(
        self,
        user_id: int,
        name: str,
        gender: str,
        city: str,
        age: int,
        interesting_gender: str,
        about: str
    ) -> int:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO profiles (user_id, name, gender, city, age, interesting_gender, about)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (user_id) DO UPDATE 
                SET name = EXCLUDED.name,
                    gender = EXCLUDED.gender,
                    city = EXCLUDED.city,
                    age = EXCLUDED.age,
                    interesting_gender = EXCLUDED.interesting_gender,
                    about = EXCLUDED.about
                RETURNING id
            """, user_id, name, gender, city, age, interesting_gender, about)
            return row["id"]

    async def save_media(self, profile_id: int, media: List[Tuple[str, str]]):
        async with self.pool.acquire() as conn:
            await conn.executemany("""
                INSERT INTO media (profile_id, type, s3_key)
                VALUES ($1, $2, $3)
            """, [(profile_id, mtype, key) for mtype, key in media])
    
    async def get_profile_by_user_id(self, user_id: int) -> Optional[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM profiles WHERE user_id = $1
            """, user_id)
            return row

    async def get_media_by_profile_id(self, profile_id: int) -> List[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT type, s3_key FROM media WHERE profile_id = $1
            """, profile_id)
            return rows
    
    async def toggle_profile_active(self, user_id: int, is_active: bool) -> bool:
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE profiles 
                SET is_active = $1
                WHERE user_id = $2
            """, is_active, user_id)
