from database.ProfileRepository import ProfileRepository
from kafka_events.producer import KafkaEventProducer
from analytics.ClickHouseLogger import ClickHouseLogger
from cache.SwipeCache import SwipeCache
from core.config import Settings
from models.api.swipe.requests import AddSwipeRequest
from models.kafka.events import SwipeEvent

class SwipeService:
    def __init__(
        self,
        repo: ProfileRepository,
        producer: KafkaEventProducer,
        logger: ClickHouseLogger,
        swipe_cache: SwipeCache,
        settings: Settings
    ):
        self.repo = repo
        self.producer = producer
        self.logger = logger
        self.cache = swipe_cache
        self.settings = settings

    async def add_swipe(self, username: str, swipe: AddSwipeRequest):
        await self.repo.save_swipe(
            from_user_id=swipe.from_user_id,
            to_user_id=swipe.to_user_id,
            action=swipe.action,
            message=swipe.message
        )

        await self.cache.add_swipe(
            swipe.from_user_id,
            swipe.to_user_id
        )

        from_profile = await self.repo.get_profile_by_user_id(swipe.from_user_id)
        to_profile = await self.repo.get_profile_by_user_id(swipe.to_user_id)

        self.logger.insert_swipe(
            from_user_id=swipe.from_user_id,
            to_user_id=swipe.to_user_id,
            action=swipe.action.lower(),
            from_city=from_profile["city"],
            to_city=to_profile["city"],
            from_gender=from_profile["gender"],
            to_gender=to_profile["gender"],
            from_age=from_profile["age"],
            to_age=to_profile["age"],
            message=swipe.message
        )

        if swipe.action in {"like", "question"}:
            event = SwipeEvent(
                from_username=username,
                from_user_id=swipe.from_user_id,
                to_user_id=swipe.to_user_id,
                action=swipe.action,
                message=swipe.message
            )
            await self.producer.send_event(self.settings.KAFKA_SWIPES_TOPIC, event.model_dump())
