import redis.asyncio as redis
from fastapi import FastAPI
from contextlib import asynccontextmanager
from pydantic import ValidationError

from database.connection import create_db_pool
from database.ProfileRepository import ProfileRepository
from storage.S3Uploader import S3Uploader
from recsys.EmbeddingRecommender import EmbeddingRecommender
from kafka_events.producer import KafkaEventProducer
from kafka_events.consumer import KafkaEventConsumer
from analytics.ClickHouseLogger import ClickHouseLogger
from utils.geo import on_geo_resolve_event
from utils.video import on_video_validation_event
from cache.SwipeCache import SwipeCache
from cache.RecommendationCache import RecommendationCache
from core.config import get_settings
from services.profile.ProfileService import ProfileService
from services.recsys.RecommendationsService import RecommendationsService
from services.media.MediaService import MediaService
from services.swipe.SwipeService import SwipeService
from models.kafka.events import LocationResolveResultEvent, VideoValidationResultEvent
from core.logger import logger

settings = get_settings()

def handle_kafka_event(event: dict, repo: ProfileRepository, recommendation_cache: RecommendationCache, producer: KafkaEventProducer):
    try:
        if 'is_human' in event:
            video_event = VideoValidationResultEvent(**event)
            return on_video_validation_event(producer, video_event)

        if 'status' in event:
            geo_event = LocationResolveResultEvent(**event)
            return on_geo_resolve_event(repo, recommendation_cache, producer, geo_event)

        raise ValueError(f"Unknown event type: {event}")
    except ValidationError as e:
        logger.error(f"Validation failed: {e.json()}")
    except Exception as e:
        logger.error(f"Unexpected error while handling event: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):

    redis_client = redis.Redis(
        host=settings.REDIS_HOST, 
        port=settings.REDIS_PORT, 
        db=settings.REDIS_FASTAPI_CACHE, 
        decode_responses=True
    )
    recommendation_cache = RecommendationCache(redis_client)
    swipe_cache = SwipeCache(redis_client)

    repo = ProfileRepository(await create_db_pool())

    producer = KafkaEventProducer(settings.kafka_bootstrap_servers)
    consumer = KafkaEventConsumer(
        settings.kafka_bootstrap_servers,
        [settings.KAFKA_GEO_TOPIC, settings.KAFKA_VIDEO_TOPIC],
        lambda event: handle_kafka_event(event, repo, recommendation_cache, producer)
    )

    recommender = EmbeddingRecommender(
        profile_repo=repo,
        recommendation_cache=recommendation_cache,
        swipe_cache=swipe_cache
    )

    uploader = S3Uploader(
        bucket_name=settings.S3_BUCKET_NAME,
        region=settings.S3_REGION_NAME,
        access_key=settings.S3_ACCESS_KEY_ID,
        secret_key=settings.S3_SECRET_ACCESS_KEY,
        endpoint_url=settings.S3_ENDPOINT_URL
    )

    logger = ClickHouseLogger(
        host=settings.CLICKHOUSE_HOST,
        port=settings.CLICKHOUSE_PORT,
        user=settings.CLICKHOUSE_USER,
        password=settings.CLICKHOUSE_PASSWORD,
        database=settings.CLICKHOUSE_DB
    )

    app.state.profile_service = ProfileService(
        repo=repo,
        producer=producer,
        recommender=recommender,
        cache=recommendation_cache,
        settings=settings
    )

    app.state.recommendations_service = RecommendationsService(
        recommender=recommender
    )

    app.state.media_service = MediaService(
        uploader=uploader,
        profile_repo=repo
    )

    app.state.swipe_service = SwipeService(
        repo=repo,
        producer=producer,
        logger=logger,
        swipe_cache=swipe_cache,
        settings=settings
    )

    await producer.start()

    await consumer.start()

    yield

    await producer.stop()
