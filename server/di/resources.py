import asyncpg
import redis.asyncio as redis
import clickhouse_driver
import boto3
from botocore.config import Config

from core.config import Settings
from di.datatypes import InfraClients, Repositories, Caches, CoreComponents, KafkaComponents, Services
from domain.media.repositories.media_repository import MediaRepository
from domain.profile.repositories.profile_repository import ProfileRepository
from domain.swipe.repositories.swipe_repository import SwipeRepository
from domain.media.services.media_service import MediaService
from domain.profile.services.profile_service import ProfileService
from domain.recommendation.services.recommendation_service import RecommendationService
from domain.swipe.services.swipe_service import SwipeService
from infrastructure.cache.redis.recommendation import RecommendationCache
from infrastructure.cache.redis.swipe import SwipeCache
from infrastructure.s3.uploader import S3Uploader
from infrastructure.messaging.kafka.consumer import KafkaEventConsumer
from infrastructure.messaging.kafka.producer import KafkaEventProducer
from infrastructure.messaging.kafka.handlers.dispatcher import handle_kafka_event
from infrastructure.db.clickhouse.logger import ClickHouseLogger
from recsys.embedding_recommender import EmbeddingRecommender

async def init_infra_clients(settings: Settings) -> InfraClients:
    postgres_pool = await asyncpg.create_pool(
        dsn=settings.postgres_dsn, 
        min_size=1, 
        max_size=10
    )

    redis_client = redis.Redis(
        host=settings.REDIS_HOST, 
        port=settings.REDIS_PORT, 
        db=settings.REDIS_FASTAPI_CACHE, 
        decode_responses=True
    )

    clickhouse_client = clickhouse_driver.Client(
        host=settings.CLICKHOUSE_HOST,
        port=settings.CLICKHOUSE_PORT,
        user=settings.CLICKHOUSE_USER,
        password=settings.CLICKHOUSE_PASSWORD,
        database=settings.CLICKHOUSE_DB
    )

    s3_client = boto3.client(
        "s3",
        region_name=settings.S3_REGION_NAME,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        endpoint_url=settings.S3_ENDPOINT_URL,
        config=Config(connect_timeout=60, read_timeout=60)
    )

    return InfraClients(
        postgres=postgres_pool,
        redis=redis_client,
        clickhouse=clickhouse_client,
        s3=s3_client,
    )

def init_repositories(pool: asyncpg.Pool) -> Repositories:
    profile_repo = ProfileRepository(pool)
    media_repo = MediaRepository(pool)
    swipe_repo = SwipeRepository(pool)

    return Repositories(
        profile=profile_repo,
        media=media_repo,
        swipe=swipe_repo
    )

def init_caches(redis: redis.Redis) -> Caches:
    recommendation_cache = RecommendationCache(redis)
    swipe_cache = SwipeCache(redis)

    return Caches(
        recommendation=recommendation_cache,
        swipe=swipe_cache
    )

def init_core_components(
    profile_repo: ProfileRepository, 
    recommendation_cache: RecommendationCache,
    swipe_cache: SwipeCache,
    s3_client: boto3.client, 
    clickhouse_client: clickhouse_driver.Client,
    settings: Settings
) -> CoreComponents:
    recommender = EmbeddingRecommender(
        profile_repo=profile_repo,
        recommendation_cache=recommendation_cache,
        swipe_cache=swipe_cache
    )

    uploader = S3Uploader(
        client=s3_client, 
        bucket_name=settings.S3_BUCKET_NAME
    )

    logger = ClickHouseLogger(clickhouse_client)

    return CoreComponents(
        recommender=recommender,
        uploader=uploader,
        logger=logger
    )

def init_kafka_components(settings: Settings, profile_repo: ProfileRepository, recommendation_cache: RecommendationCache) -> KafkaComponents:
    producer = KafkaEventProducer(settings.kafka_bootstrap_servers)
    consumer = KafkaEventConsumer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        topics=[settings.KAFKA_GEO_TOPIC, settings.KAFKA_VIDEO_TOPIC],
        callback=lambda event: handle_kafka_event(event, profile_repo, recommendation_cache, producer, settings)
    )

    return KafkaComponents(
        producer=producer,
        consumer=consumer
    )

def init_services(
    profile_repo: ProfileRepository,
    media_repo: MediaRepository,
    swipe_repo: SwipeRepository,
    recommendation_cache: RecommendationCache,
    swipe_cache: SwipeCache,
    recommender: EmbeddingRecommender,
    uploader: S3Uploader,
    logger: ClickHouseLogger,
    producer: KafkaEventProducer,
    settings: Settings
) -> Services:
    profile_service = ProfileService(
        profile_repo=profile_repo,
        producer=producer,
        recommender=recommender,
        cache=recommendation_cache,
        settings=settings
    )

    recommendation_service = RecommendationService(recommender)

    media_service = MediaService(
        uploader=uploader,
        media_repo=media_repo,
        profile_repo=profile_repo
    )

    swipe_service = SwipeService(
        swipe_repo=swipe_repo,
        producer=producer,
        logger=logger,
        swipe_cache=swipe_cache,
        settings=settings
    )

    return Services(
        profile=profile_service,
        media=media_service,
        recommendation=recommendation_service,
        swipe=swipe_service
    )
