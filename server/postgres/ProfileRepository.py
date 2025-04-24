import asyncpg
import numpy as np
from typing import List, Tuple, Optional

class ProfileRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def save_profile(
        self,
        user_id: int,
        name: str,
        gender: str,
        city: Optional[str],
        age: int,
        interesting_gender: str,
        about: str,
        latitude: float,
        longitude: float
    ) -> int:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO profiles (
                    user_id, name, gender, city, age, 
                    interesting_gender, about, latitude, longitude,
                    location
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9,
                    ST_SetSRID(ST_MakePoint($9, $8), 4326)::geography)
                ON CONFLICT (user_id) DO UPDATE 
                SET name = EXCLUDED.name,
                    gender = EXCLUDED.gender,
                    city = EXCLUDED.city,
                    age = EXCLUDED.age,
                    interesting_gender = EXCLUDED.interesting_gender,
                    about = EXCLUDED.about,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    location = ST_SetSRID(ST_MakePoint(EXCLUDED.longitude, EXCLUDED.latitude), 4326)::geography
                RETURNING id
            """, user_id, name, gender, city, age, interesting_gender, about, latitude, longitude)
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
    
    async def toggle_profile_active(self, user_id: int, is_active: bool):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE profiles 
                SET is_active = $1
                WHERE user_id = $2
            """, is_active, user_id)
    
    async def update_profile_field(self, user_id: int, field_name: str, value):
        async with self.pool.acquire() as conn:
            query = f"""
                UPDATE profiles
                SET {field_name} = $1
                WHERE user_id = $2
            """
            await conn.execute(query, value, user_id)
    
    async def delete_media_by_profile_id(self, profile_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM media WHERE profile_id = $1
            """, profile_id)
    
    async def update_embedding(self, user_id: int, embedding: np.ndarray):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE profiles 
                SET about_embedding = $1 
                WHERE user_id = $2
            """, embedding.tolist(), user_id)
    
    async def get_candidates_with_embeddings(
        self,
        user_id: int,
        user: dict,
        max_distance: int,
        min_age: int,
        max_age: int
    ) -> List[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            candidates = await conn.fetch(
                """
                SELECT *, ST_Distance(location, ST_MakePoint($2, $1)::geography) AS dist
                FROM profiles 
                WHERE user_id != $3
                AND is_active = TRUE
                AND location IS NOT NULL
                AND ST_DWithin(location, ST_MakePoint($2, $1)::geography, $4)
                AND about_embedding IS NOT NULL
                AND gender = ANY(
                    CASE 
                        WHEN $5 = 'any' THEN ARRAY['male'::gender, 'female'::gender]
                        ELSE ARRAY[$5::gender]
                    END
                )
                AND age BETWEEN $6 AND $7
                AND user_id NOT IN (
                    SELECT to_user_id FROM swipes WHERE from_user_id = $3
                )
                LIMIT 100
                """,
                user['latitude'], user['longitude'], user_id, max_distance * 1000,
                user['interesting_gender'], min_age, max_age
            )
            return candidates


    async def get_candidates_by_criteria(
        self,
        user_id: int,
        user: dict,
        rec_list: List[int],
        min_age: int,
        max_age: int
    ) -> List[int]:
        async with self.pool.acquire() as conn:
            records = await conn.fetch(
                """
                SELECT * FROM profiles 
                WHERE user_id != $1
                AND user_id != ANY($5::int[])
                AND is_active = TRUE
                AND city = $2
                AND gender = ANY(
                    CASE 
                        WHEN $3 = 'any' THEN ARRAY['male'::gender, 'female'::gender]
                        ELSE ARRAY[$3::gender]
                    END
                )
                AND age BETWEEN $6 AND $7
                AND user_id NOT IN (
                    SELECT to_user_id FROM swipes WHERE from_user_id = $1
                )
                """,
                user_id,
                user["city"],
                user["interesting_gender"],
                rec_list,
                min_age,
                max_age
            )
            return [record['user_id'] for record in records]


    async def save_swipe(
        self,
        from_user_id: int,
        to_user_id: int,
        action: str,
        message: Optional[str] = None
    ):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO swipes (from_user_id, to_user_id, action, message)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (from_user_id, to_user_id) DO UPDATE
                SET action = EXCLUDED.action,
                    message = EXCLUDED.message
            """, from_user_id, to_user_id, action, message)
