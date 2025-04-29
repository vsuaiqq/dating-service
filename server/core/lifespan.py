import redis.asyncio as redis
from fastapi import FastAPI
from contextlib import asynccontextmanager

from database.connection import create_db_pool
from database.ProfileRepository import ProfileRepository
from storage.S3Uploader import S3Uploader
from services.recsys.recsys import EmbeddingRecommender
from kafka_events.producer import KafkaEventProducer
from kafka_events.consumer import KafkaEventConsumer
from analytics.ClickHouseLogger import ClickHouseLogger
from utils.geo import on_geo_resolve_event
from cache.SwipeCache import SwipeCache
from cache.RecommendationCache import RecommendationCache
from core.config import get_settings

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = redis.Redis(
        host=settings.REDIS_HOST, 
        port=settings.REDIS_PORT, 
        db=settings.REDIS_FASTAPI_CACHE, 
        decode_responses=True
    )

    kafka_bootstrap_servers = settings.kafka_bootstrap_servers

    app.state.profile_repo = ProfileRepository(await create_db_pool())

    app.state.s3_uploader = S3Uploader(
        bucket_name=settings.S3_BUCKET_NAME,
        region=settings.S3_REGION_NAME,
        access_key=settings.S3_ACCESS_KEY_ID,
        secret_key=settings.S3_SECRET_ACCESS_KEY,
        endpoint_url=settings.S3_ENDPOINT_URL
    )

    app.state.recommendation_cache = RecommendationCache(redis_client)

    app.state.swipe_cache = SwipeCache(redis_client)

    app.state.recsys = EmbeddingRecommender(
        profile_repo=app.state.profile_repo,
        recommendation_cache=app.state.recommendation_cache,
        swipe_cache=app.state.swipe_cache
    )

    app.state.kafka_producer = KafkaEventProducer(kafka_bootstrap_servers)

    app.state.clickhouse_logger = ClickHouseLogger(
        host=settings.CLICKHOUSE_HOST,
        port=settings.CLICKHOUSE_PORT,
        user=settings.CLICKHOUSE_USER,
        password=settings.CLICKHOUSE_PASSWORD,
        database=settings.CLICKHOUSE_DB
    )

    kafka_consumer = KafkaEventConsumer(
        kafka_bootstrap_servers,
        [settings.KAFKA_GEO_TOPIC],
        lambda event: on_geo_resolve_event(
            app.state.profile_repo, 
            app.state.recommendation_cache, 
            app.state.kafka_producer,
            event
        )
    )

    await app.state.kafka_producer.start()

    await kafka_consumer.start()

    yield

    await app.state.kafka_producer.stop()
