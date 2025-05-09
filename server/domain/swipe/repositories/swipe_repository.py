import asyncpg
from typing import Optional

class SwipeRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

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
