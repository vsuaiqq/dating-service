import asyncio
import redis.asyncio as redis
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_FSM, S3_ACCESS_KEY_ID, S3_BUCKET_NAME, S3_ENDPOINT_URL, S3_REGION_NAME, S3_SECRET_ACCESS_KEY
from db.ProfileRepository import ProfileRepository
from s3.S3Uploader import S3Uploader
from db.connection import create_db_pool
from utils.logger import setup_logger
from handlers import all_handlers
from middlewares.i18n import I18nMiddleware

async def main():
    setup_logger()

    pool = await create_db_pool()
    profile_repo = ProfileRepository(pool)

    s3_uploader = S3Uploader(
        bucket_name=S3_BUCKET_NAME,
        region=S3_REGION_NAME,
        access_key=S3_ACCESS_KEY_ID,
        secret_key=S3_SECRET_ACCESS_KEY,
        endpoint_url=S3_ENDPOINT_URL
    )

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_FSM)
    redis_storage = RedisStorage(redis_client)
    dp = Dispatcher(storage=redis_storage)

    for router in all_handlers:
        router.profile_repo = profile_repo
        router.s3_uploader = s3_uploader
        dp.include_router(router)

    dp.message.middleware(I18nMiddleware())
    dp.callback_query.middleware(I18nMiddleware())
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
