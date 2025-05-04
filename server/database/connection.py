import asyncpg
from core.logger import logger
from core.config import get_settings

settings = get_settings()

async def create_db_pool() -> asyncpg.Pool:
    try:
        pool =  await asyncpg.create_pool(dsn=settings.postgres_dsn, min_size=1, max_size=10)
        logger.info("POSTGRES connection success.")
        return pool
    except Exception as e:
        logger.error(f"Failed to connect POSTGRES: {e}")
        raise
