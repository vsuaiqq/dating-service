import redis.asyncio as redis
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from config import (
    BOT_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_FSM,
    API_URL, KAFKA_GEO_NOTIFICATIONS_TOPIC, KAFKA_SWIPES_TOPIC, KAFKA_VIDEO_NOTIFICATIONS_TOPIC
)
from utils.logger import setup_logger
from handlers import all_handlers
from middlewares.i18n import I18nMiddleware
from api.ProfileClient import ProfileClient
from api.S3Client import S3Client
from api.RecSysClient import RecSysClient
from api.SwipeClient import SwipeClient
from kafka_events.consumer import KafkaEventConsumer
from keyboards.back import get_back_keyboard
from states.profile import ProfileStates
from aiogram.types import InputMediaPhoto, InputMediaVideo

class TelegramBot:
    def __init__(self):
        setup_logger()
        self._init_clients()
        self._init_bot()
        self._init_dispatcher()
        self._init_kafka_consumer()

    def _init_clients(self):
        self.profile_client = ProfileClient(API_URL)
        self.s3_client = S3Client(API_URL)
        self.recsys_client = RecSysClient(API_URL)
        self.swipe_client = SwipeClient(API_URL)

    def _init_bot(self):
        self.bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )

    def _init_dispatcher(self):
        redis_instance = redis.Redis(
            host='localhost',
            port=REDIS_PORT,
            db=REDIS_FSM
        )
        self.dp = Dispatcher(storage=RedisStorage(redis_instance))
        self.dp = Dispatcher(storage=MemoryStorage())
        self.dp.message.middleware(I18nMiddleware())
        self.dp.callback_query.middleware(I18nMiddleware())

        self._register_routers()

    def _register_routers(self):
        for router in all_handlers:
            router.profile_client = self.profile_client
            router.s3_client = self.s3_client
            router.recsys_client = self.recsys_client
            router.swipe_client = self.swipe_client
            self.dp.include_router(router)

    def _init_kafka_consumer(self):
        self.kafka_consumer = KafkaEventConsumer(
            bootstrap_servers="localhost:29092",
            topics=[KAFKA_SWIPES_TOPIC, KAFKA_GEO_NOTIFICATIONS_TOPIC, KAFKA_VIDEO_NOTIFICATIONS_TOPIC],
            callback=self._handle_kafka_event
        )
    
    async def _show_profile(self, from_user_id: int, to_user_id: int):
        profile = await self.profile_client.get_profile_by_user_id(from_user_id)

        media_list = await self.profile_client.get_media_by_profile_id(from_user_id)
        if profile.city is None:
            profile_text = f"{profile.name}, {profile.age} - {profile.about} {'active_status' if profile.is_active else 'inactive_status'}"
        else:
            profile_text = f"{profile.name}, {profile.age}, {profile.city} - {profile.about} {'active_status' if profile.is_active else 'inactive_status'}"

        media_objects = []
        
        for i, media in enumerate(media_list.media):
            media_url = await self.s3_client.get_presigned_url(media.s3_key)
            if media.type == "photo":
                media_obj = InputMediaPhoto(media=media_url.url, caption=profile_text if i == 0 else None)
            else:
                media_obj = InputMediaVideo(media=media_url.url, caption=profile_text if i == 0 else None)
            media_objects.append(media_obj)

        try:
            await self.bot.send_message(to_user_id, "profile_preview")
            await self.bot.send_media_group(to_user_id, media=media_objects)
            return True
        except Exception as e:
            await self.bot.send_message(to_user_id, "preview_error" + f": {str(e)}")
            return False

    async def _handle_kafka_event(self, event: dict):
        if 'action' in event:
            await self._handle_swipe_event(event)
        elif 'is_human' in event:
            await self._handle_video_notification(event)
        else:
            await self._handle_geo_notification(event)

    async def _handle_swipe_event(self, event: dict):
        text = ""
        if event['action'] == "like":
            text = "💖 Вам поставили лайк!"
        elif event['action'] == "question":
            text = f"💖 Вам поставили лайк!: {event['message']}"

        await self.bot.send_message(
            event['to_user_id'],
            text,
            parse_mode=ParseMode.HTML
        )
        await self._show_profile(event['from_user_id'], event['to_user_id'])

    async def _handle_geo_notification(self, event: dict):
        messages = {
            "waited": "Ищем подходящие анкеты... Пожалуйста, подождите немного. Пока вы можете смотреть случайные анкеты",
            "success": "Всё готово! Рекомендации настроены",
            "failed": "Не удалось определить ваше местоположение. Пожалуйста, попробуйте еще раз или отправьте вашу текущую локацию, также вы можете продолжить смотреть случайные анкеты"
        }
        await self.bot.send_message(
            event['user_id'],
            messages.get(event['status'], "Неизвестный статус"),
            parse_mode=ParseMode.HTML
        )
    
    async def _handle_video_notification(self, event: dict):
        user_id = event['user_id']
        is_human = event.get('is_human', False)

        state = self.dp.fsm.get_context(user_id=user_id, chat_id=user_id, bot=self.bot)
        
        if is_human:
            await self.bot.send_message(user_id, "verification_success")
            await self.bot.send_message(user_id, "ask age")
            await state.set_state(ProfileStates.age)
        else:
            await self.bot.send_message(user_id, "verification_failed")

    async def run(self):
        await self.kafka_consumer.start()
        await self.dp.start_polling(self.bot)
