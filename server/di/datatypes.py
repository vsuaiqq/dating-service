import redis.asyncio as redis
import asyncpg
import clickhouse_driver
import boto3
from dataclasses import dataclass

from domain.media.repositories.media_repository import MediaRepository
from domain.profile.repositories.profile_repository import ProfileRepository
from domain.swipe.repositories.swipe_repository import SwipeRepository
from domain.media.services.media_service import MediaService
from domain.profile.services.profile_service import ProfileService
from domain.recommendation.services.recommendation_service import RecommendationService
from domain.swipe.services.swipe_service import SwipeService
from infrastructure.cache.redis.recommendation_cache import RecommendationCache
from infrastructure.cache.redis.swipe_cache import SwipeCache
from infrastructure.storage.s3.s3_uploader import S3Uploader
from infrastructure.messaging.kafka.consumer import KafkaEventConsumer
from infrastructure.messaging.kafka.producer import KafkaEventProducer
from infrastructure.db.clickhouse.clickhouse_logger import ClickHouseLogger
from recsys.embedding_recommender import EmbeddingRecommender

@dataclass
class InfraClients:
    postgres: asyncpg.Pool
    redis: redis.Redis
    clickhouse: clickhouse_driver.Client
    s3: boto3.client

@dataclass
class Repositories:
    profile: ProfileRepository
    media: MediaRepository
    swipe: SwipeRepository

@dataclass
class Caches:
    recommendation: RecommendationCache
    swipe: SwipeCache

@dataclass
class KafkaComponents:
    producer: KafkaEventProducer
    consumer: KafkaEventConsumer

@dataclass
class CoreComponents:
    recommender: EmbeddingRecommender
    uploader: S3Uploader
    logger: ClickHouseLogger

@dataclass
class Services:
    profile: ProfileService
    media: MediaService
    recommendation: RecommendationService
    swipe: SwipeService
