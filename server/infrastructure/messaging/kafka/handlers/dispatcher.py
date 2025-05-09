from pydantic import ValidationError

from domain.profile.repositories.profile_repository import ProfileRepository
from infrastructure.messaging.kafka.producer import KafkaEventProducer
from infrastructure.messaging.kafka.handlers.geo import on_geo_resolve_event
from infrastructure.messaging.kafka.handlers.video import on_video_validation_event
from infrastructure.cache.redis.recommendation import RecommendationCache
from contracts.kafka.events import LocationResolveResultEvent, VideoValidationResultEvent
from core.config import Settings
from core.logger import logger

async def handle_kafka_event(
    event: dict,
    profile_repo: ProfileRepository,
    recommendation_cache: RecommendationCache,
    producer: KafkaEventProducer,
    settings: Settings
):
    try:
        if 'is_human' in event:
            video_event = VideoValidationResultEvent(**event)
            return await on_video_validation_event(video_event, producer, settings)

        if 'status' in event:
            geo_event = LocationResolveResultEvent(**event)
            return await on_geo_resolve_event(geo_event, profile_repo, recommendation_cache, producer, settings)

        raise ValueError(f"Unknown event type: {event}")

    except ValidationError as e:
        logger.error(f"Validation failed: {e.json()}")
    except Exception as e:
        logger.error(f"Unexpected error while handling event: {e}")
