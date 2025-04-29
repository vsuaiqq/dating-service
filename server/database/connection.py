import asyncpg
import logging
from core.config import POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, DB_PORT, DB_HOST

async def create_db_pool() -> asyncpg.Pool:
    try:
        dsn = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB}"
        pool =  await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=10)
        logging.info("Успешное подключение к базе данных.")
        return pool
    except Exception as e:
        logging.error(f"Ошибка при подключении к базе данных: {e}")
        raise
