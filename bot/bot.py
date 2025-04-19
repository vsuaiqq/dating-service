import asyncio
import redis.asyncio as redis
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_FSM, API_URL
from utils.logger import setup_logger
from handlers import all_handlers
from middlewares.i18n import I18nMiddleware
from api.ProfileClient import ProfileClient
from api.S3Client import S3Client

async def main():
    setup_logger()

    profile_client = ProfileClient(API_URL)
    s3_client = S3Client(API_URL)

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_FSM)
    redis_storage = RedisStorage(redis_client)
    dp = Dispatcher(storage=redis_storage)

    dp.message.middleware(I18nMiddleware())
    dp.callback_query.middleware(I18nMiddleware())
    
    for router in all_handlers:
        router.profile_client = profile_client
        router.s3_client = s3_client
        dp.include_router(router)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
