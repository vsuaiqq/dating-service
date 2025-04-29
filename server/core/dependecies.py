from fastapi import Request

from database.ProfileRepository import ProfileRepository
from cloud_storage.S3Uploader import S3Uploader
from recsys.recsys import EmbeddingRecommender
from kafka_events.producer import KafkaEventProducer
from clickhouse.ClickHouseLogger import ClickHouseLogger
from geo.CachedLocationResolver import CachedLocationResolver
from cache.SwipeCache import SwipeCache
from cache.RecommendationCache import RecommendationCache

def get_profile_repo(request: Request) -> ProfileRepository:
    return request.app.state.profile_repo

def get_s3_uploader(request: Request) -> S3Uploader:
    return request.app.state.s3_uploader

def get_recommender(request: Request) -> EmbeddingRecommender:
    return request.app.state.recsys

def get_kafka_producer(request: Request) -> KafkaEventProducer:
    return request.app.state.kafka_producer

def get_clickhouse_logger(request: Request) -> ClickHouseLogger:
    return request.app.state.clickhouse_logger

def get_cached_location_resolver(request: Request) -> CachedLocationResolver:
    return request.app.state.cached_location_resolver

def get_swipe_cache(request: Request) -> SwipeCache:
    return request.app.state.swipe_cache

def get_recommendation_cache(request: Request) -> RecommendationCache:
    return request.app.state.recommendation_cache
