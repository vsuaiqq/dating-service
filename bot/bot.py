import asyncio
import redis.asyncio as redis
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_FSM, API_URL, NUM_OF_RECS
from utils.logger import setup_logger
from handlers import all_handlers
from middlewares.i18n import I18nMiddleware
from api.ProfileClient import ProfileClient
from api.S3Client import S3Client
from api.RecSysClient import RecSysClient
from api.SwipeClient import SwipeClient

from kafka_events.consumer import KafkaEventConsumer

async def main():
    setup_logger()

    profile_client = ProfileClient(API_URL)
    s3_client = S3Client(API_URL)
    recsys_client = RecSysClient(API_URL, NUM_OF_RECS)
    swipe_client = SwipeClient(API_URL)

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=RedisStorage(redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_FSM)))

    dp.message.middleware(I18nMiddleware())
    dp.callback_query.middleware(I18nMiddleware())

    async def handle_swipe_event(event):
        text = ""
        if event['action'] == "like":
            text = f"💖 Вам поставили лайк!"
        elif event['action'] == "question":
            text = f"❓ Вам задали вопрос: {event['message'] or 'Без текста'}"
        await bot.send_message(event['to_user_id'], text, parse_mode=ParseMode.HTML)
    
    kafka = KafkaEventConsumer("localhost:9092", "swipes", callback=handle_swipe_event)

    await kafka.start()

    for router in all_handlers:
        router.profile_client = profile_client
        router.s3_client = s3_client
        router.recsys_client = recsys_client
        router.swipe_client = swipe_client
        dp.include_router(router)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
