import asyncpg
from typing import List, Tuple, Optional

class ProfileRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def save_profile(
        self,
        telegram_id: int,
        phone_number: str,
        username: Optional[str],
        age: int,
        gender: str,
        preferred_gender: str,
        city: str,
        about: str
    ) -> int:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO users (
                    telegram_id, phone_number, username, age, gender, 
                    preferred_gender, city, about
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (telegram_id) DO UPDATE 
                SET phone_number = EXCLUDED.phone_number,
                    username = EXCLUDED.username,
                    age = EXCLUDED.age,
                    gender = EXCLUDED.gender,
                    preferred_gender = EXCLUDED.preferred_gender,
                    city = EXCLUDED.city,
                    about = EXCLUDED.about,
                    last_online = CURRENT_TIMESTAMP
                RETURNING id
            """, telegram_id, phone_number, username, age, gender, 
                preferred_gender, city, about)
            return row["id"]

    async def save_media(self, user_id: int, file_id: str, is_main: bool = False):
        async with self.pool.acquire() as conn:
            # Если устанавливаем новое главное фото, сначала сбросим все предыдущие
            if is_main:
                await conn.execute("""
                    UPDATE user_photos 
                    SET is_main = FALSE 
                    WHERE user_id = $1
                """, user_id)
            
            await conn.execute("""
                INSERT INTO user_photos (user_id, file_id, is_main)
                VALUES ($1, $2, $3)
            """, user_id, file_id, is_main)

    async def get_profile_by_user_id(self, user_id: int) -> Optional[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT 
                    u.id, u.telegram_id, u.phone_number, u.username, 
                    u.age, u.gender, u.preferred_gender, u.city, u.about, u.is_active,
                    (SELECT file_id FROM user_photos 
                     WHERE user_id = u.telegram_id AND is_main = TRUE LIMIT 1) as main_photo
                FROM users u
                WHERE u.telegram_id = $1
            """, user_id)
            return row

    async def get_user_photos(self, user_id: int) -> List[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, file_id, is_main, uploaded_at 
                FROM user_photos 
                WHERE user_id = $1
                ORDER BY is_main DESC, uploaded_at DESC
            """, user_id)
            return rows

    async def toggle_profile_active(self, user_id: int, is_active: bool):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE users 
                SET is_active = $1,
                    last_online = CURRENT_TIMESTAMP
                WHERE telegram_id = $2
            """, is_active, user_id)

    async def update_profile_field(self, user_id: int, field_name: str, value):
        async with self.pool.acquire() as conn:
            valid_fields = {
                'phone_number', 'username', 'age', 'gender',
                'preferred_gender', 'city', 'about'
            }
            
            if field_name not in valid_fields:
                raise ValueError(f"Invalid field name: {field_name}")
            
            await conn.execute(f"""
                UPDATE users
                SET {field_name} = $1,
                    last_online = CURRENT_TIMESTAMP
                WHERE telegram_id = $2
            """, value, user_id)

    async def delete_user_photo(self, photo_id: int, user_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM user_photos 
                WHERE id = $1 AND user_id = $2
            """, photo_id, user_id)

    async def set_main_photo(self, photo_key: str, user_id: int):
        async with self.pool.acquire() as conn:
            # Сбрасываем все is_main
            await conn.execute("""
                UPDATE user_photos 
                SET is_main = FALSE 
                WHERE user_id = $1
            """, user_id)
            
            # Устанавливаем новое главное фото
            await conn.execute("""
                UPDATE user_photos 
                SET is_main = TRUE 
                WHERE file_id = $1 AND user_id = $2
            """, photo_key, user_id)

    async def update_photo(self, photo_key: str, user_id: int, is_main: bool):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE user_photos 
                SET is_main = $1 
                WHERE file_id = $2 AND user_id = $3
            """, is_main, photo_key, user_id)
    async def delete_media_by_key(self, key: str):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM user_photos WHERE file_id = $1", key)

    async def bulk_delete_media(self, keys: List[str]):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM user_photos WHERE file_id = ANY($1)", keys)

    async def record_swipe(
        self,
        from_user_id: int,
        to_user_id: int,
        action: str,
        message: Optional[str] = None
    ) -> bool:
        async with self.pool.acquire() as conn:
            try:
                await conn.execute("""
                    INSERT INTO swipes (
                        from_user_id, to_user_id, action, message
                    )
                    VALUES ($1, $2, $3, $4)
                """, from_user_id, to_user_id, action, message)
                
                if action == 'like':
                    mutual_like = await conn.fetchval("""
                        SELECT 1 FROM swipes 
                        WHERE from_user_id = $1 AND to_user_id = $2 AND action = 'like'
                    """, to_user_id, from_user_id)
                    
                    if mutual_like:
                        await conn.execute("""
                            INSERT INTO matches (user1_id, user2_id)
                            VALUES ($1, $2)
                            ON CONFLICT DO NOTHING
                        """, min(from_user_id, to_user_id), 
                           max(from_user_id, to_user_id))
                        return True
                return False
            except asyncpg.UniqueViolationError:
                return False

    async def get_user_matches(self, user_id: int, limit: int = 100) -> List[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    CASE 
                        WHEN m.user1_id = $1 THEN m.user2_id
                        ELSE m.user1_id
                    END as match_user_id,
                    u.username,
                    u.age,
                    u.city,
                    (SELECT file_id FROM user_photos 
                     WHERE user_id = CASE 
                        WHEN m.user1_id = $1 THEN m.user2_id
                        ELSE m.user1_id
                     END AND is_main = TRUE LIMIT 1) as main_photo
                FROM matches m
                JOIN users u ON (
                    (m.user1_id = u.telegram_id AND m.user1_id != $1) OR
                    (m.user2_id = u.telegram_id AND m.user2_id != $1)
                )
                WHERE m.user1_id = $1 OR m.user2_id = $1
                ORDER BY m.created_at DESC
                LIMIT $2
            """, user_id, limit)
            return rows
        
    async def check_match(self, user1_id: int, user2_id: int) -> bool:
        async with self.pool.acquire() as conn:
            return await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM swipes
                    WHERE from_user_id = $1 AND to_user_id = $2 AND action = 'like'
                )
            """, user2_id, user1_id)