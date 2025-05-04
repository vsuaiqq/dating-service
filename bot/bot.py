import redis.asyncio as redis
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InputMediaPhoto, InputMediaVideo
from pydantic import ValidationError

from config import (
    BOT_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_FSM,
    API_URL, KAFKA_GEO_NOTIFICATIONS_TOPIC, KAFKA_SWIPES_TOPIC, KAFKA_VIDEO_NOTIFICATIONS_TOPIC
)
from utils.logger import setup_logger
from handlers import all_handlers
from middlewares.i18n import I18nMiddleware
from api.ProfileClient import ProfileClient
from api.MediaClient import MediaClient
from api.RecSysClient import RecSysClient
from api.SwipeClient import SwipeClient
from kafka_events.consumer import KafkaEventConsumer
from keyboards.back import get_back_keyboard
from states.profile import ProfileStates
from utils.i18n import get_translator
from models.kafka.events import SwipeEvent, VideoValidationResultEvent, LocationResolveResultEvent

class TelegramBot:
    def __init__(self):
        setup_logger()
        self._init_clients()
        self._init_bot()
        self._init_dispatcher()
        self._init_kafka_consumer()

    def _init_clients(self):
        self.profile_client = ProfileClient(API_URL)
        self.media_client = MediaClient(API_URL)
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
            router.media_client = self.media_client
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

        _ = get_translator(await self.bot.get_chat(to_user_id))

        if profile.city is None:
            profile_text = f"{profile.name}, {profile.age} - {profile.about}"
        else:
            profile_text = f"{profile.name}, {profile.age}, {profile.city} - {profile.about}"

        media_objects = []
        
        for i, media in enumerate(media_list.media):
            media_url = await self.media_client.get_presigned_url(media.s3_key)
            if media.type == "photo":
                media_obj = InputMediaPhoto(media=media_url.url, caption=profile_text if i == 0 else None)
            else:
                media_obj = InputMediaVideo(media=media_url.url, caption=profile_text if i == 0 else None)
            media_objects.append(media_obj)

        try:
            await self.bot.send_media_group(to_user_id, media=media_objects)
            return True
        except Exception as e:
            await self.bot.send_message(to_user_id, "preview_error" + f": {str(e)}")
            return False

    async def _handle_kafka_event(self, event: dict):
        print('\n\n', event, '\n\n')
        try:
            if 'action' in event:
                swipe_event = SwipeEvent(**event)
                await self._handle_swipe_event(swipe_event)
                return

            if 'is_human' in event:
                video_event = VideoValidationResultEvent(**event)
                await self._handle_video_notification(video_event)
                return

            if 'status' in event:
                geo_event = LocationResolveResultEvent(**event)
                await self._handle_geo_notification(geo_event)
                return

            raise ValueError(f"Unknown event type: {event}")
        except ValidationError as e:
            print(f"Validation failed: {e.json()}")
        except Exception as e:
            print(f"Unexpected error while handling event: {e}")

    async def _handle_swipe_event(self, event: SwipeEvent):
        text = ""
        if event.action == "like":
            text = "💖 Вам поставили лайк!"
        elif event.action == "question":
            text = f"💖 Вам поставили лайк!: {event.message}"

        from_username = event.from_username

        await self.bot.send_message(
            event.to_user_id,
            text,
            parse_mode=ParseMode.HTML
        )
        await self._show_profile(event.from_user_id, event.to_user_id)
        await self.bot.send_message(
            event.to_user_id, 
            f'<a href="t.me/{from_username}">Открыть профиль</a>',
            parse_mode="HTML"
        )

    async def _handle_geo_notification(self, event: LocationResolveResultEvent):
        user_id = event.user_id
        _ = get_translator(await self.bot.get_chat(user_id))
        await self.bot.send_message(
            user_id,
            _(f"geo_notification_{event.status}"),
            parse_mode=ParseMode.HTML
        )
    
    async def _handle_video_notification(self, event: VideoValidationResultEvent):
        user_id = event.user_id
        is_human = event.is_human

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
