import redis.asyncio as redis
from fastapi import FastAPI
from contextlib import asynccontextmanager

from database.connection import create_db_pool
from database.ProfileRepository import ProfileRepository
from cloud_storage.S3Uploader import S3Uploader
from recsys.recsys import EmbeddingRecommender
from kafka_events.producer import KafkaEventProducer
from kafka_events.consumer import KafkaEventConsumer
from clickhouse.ClickHouseLogger import ClickHouseLogger
from geo.CachedLocationResolver import CachedLocationResolver
from geo.LocationResolver import LocationResolver
from workers.geo_worker import handle_geo_request
from cache.CityCoordinatesCache import CityCoordinatesCache
from cache.SwipeCache import SwipeCache
from cache.RecommendationCache import RecommendationCache

from core.config import (
    S3_BUCKET_NAME, S3_REGION_NAME, S3_ACCESS_KEY_ID,
    S3_SECRET_ACCESS_KEY, S3_ENDPOINT_URL, 
    CLICKHOUSE_DB, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD,
    CLICKHOUSE_HOST, CLICKHOUSE_PORT,
    REDIS_HOST, REDIS_PORT, REDIS_FASTAPI_CACHE,
    KAFKA_HOST, KAFKA_PORT, KAFKA_GEO_TOPIC
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_FASTAPI_CACHE, decode_responses=True)

    app.state.profile_repo = ProfileRepository(await create_db_pool())
    app.state.s3_uploader = S3Uploader(
        bucket_name=S3_BUCKET_NAME,
        region=S3_REGION_NAME,
        access_key=S3_ACCESS_KEY_ID,
        secret_key=S3_SECRET_ACCESS_KEY,
        endpoint_url=S3_ENDPOINT_URL
    )
    app.state.recommendation_cache = RecommendationCache(redis_client)
    app.state.swipe_cache = SwipeCache(redis_client)
    app.state.recsys = EmbeddingRecommender(
        profile_repo=app.state.profile_repo,
        recommendation_cache=app.state.recommendation_cache,
        swipe_cache=app.state.swipe_cache
    )
    app.state.kafka_producer = KafkaEventProducer(f"{KAFKA_HOST}:{KAFKA_PORT}")
    app.state.clickhouse_logger = ClickHouseLogger(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        user=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DB
    )
    app.state.cached_location_resolver = CachedLocationResolver(
        resolver=LocationResolver(),
        cache=CityCoordinatesCache(redis_client)
    )

    kafka_consumer = KafkaEventConsumer(
        f"{KAFKA_HOST}:{KAFKA_PORT}",
        KAFKA_GEO_TOPIC,
        lambda event: handle_geo_request(
            app.state.profile_repo, 
            app.state.cached_location_resolver, 
            app.state.recommendation_cache, 
            app.state.kafka_producer,
            event
        )
    )

    await app.state.kafka_producer.start()

    await kafka_consumer.start()

    yield

    await app.state.kafka_producer.stop()
