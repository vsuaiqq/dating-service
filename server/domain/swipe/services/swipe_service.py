from core.config import Settings
from domain.swipe.repositories.swipe_repository import SwipeRepository
from domain.profile.services.profile_service import ProfileService
from infrastructure.messaging.kafka.producer import KafkaEventProducer
from infrastructure.db.clickhouse.clickhouse_logger import ClickHouseLogger
from infrastructure.cache.redis.swipe_cache import SwipeCache
from api.v1.schemas.swipe import AddSwipeRequest
from contracts.kafka.events import SwipeEvent

class SwipeService:
    def __init__(
        self,
        swipe_repo: SwipeRepository,
        profile_service: ProfileService,
        producer: KafkaEventProducer,
        logger: ClickHouseLogger,
        swipe_cache: SwipeCache,
        settings: Settings
    ):
        self.swipe_repo = swipe_repo
        self.profile_service = profile_service
        self.producer = producer
        self.logger = logger
        self.cache = swipe_cache
        self.settings = settings

    async def add_swipe(self, username: str, swipe: AddSwipeRequest):
        await self.swipe_repo.save_swipe(
            from_user_id=swipe.from_user_id,
            to_user_id=swipe.to_user_id,
            action=swipe.action,
            message=swipe.message
        )

        await self.cache.set(
            swipe.from_user_id,
            swipe.to_user_id
        )

        from_profile = await self.profile_service.get_profile_by_user_id(swipe.from_user_id)
        to_profile = await self.profile_service.get_profile_by_user_id(swipe.to_user_id)

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
