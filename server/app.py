import redis.asyncio as redis
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, model_validator
from typing import List, Optional
from fastapi import UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from io import BytesIO
import datetime

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

from config import (
    S3_BUCKET_NAME, S3_REGION_NAME, S3_ACCESS_KEY_ID,
    S3_SECRET_ACCESS_KEY, S3_ENDPOINT_URL, 
    CLICKHOUSE_DB, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD,
    CLICKHOUSE_HOST, CLICKHOUSE_PORT,
    REDIS_HOST, REDIS_PORT, REDIS_FASTAPI_CACHE,
    KAFKA_HOST, KAFKA_PORT, KAFKA_SWIPES_TOPIC, KAFKA_GEO_TOPIC, KAFKA_GEO_NOTIFICATIONS_TOPIC,
    KAFKA_PROFILE_UPDATES_TOPIC
)

ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_FASTAPI_CACHE, decode_responses=True)
    recommendation_cache = RecommendationCache(redis_client)

    app.state.profile_repo = ProfileRepository(await create_db_pool())
    app.state.s3_uploader = S3Uploader(
        bucket_name=S3_BUCKET_NAME,
        region=S3_REGION_NAME,
        access_key=S3_ACCESS_KEY_ID,
        secret_key=S3_SECRET_ACCESS_KEY,
        endpoint_url=S3_ENDPOINT_URL
    )
    app.state.swipe_cache = SwipeCache(redis_client)
    app.state.recsys = EmbeddingRecommender(
        profile_repo=app.state.profile_repo,
        recommendation_cache=recommendation_cache,
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
            recommendation_cache, 
            app.state.kafka_producer,
            event
        )
    )

    await app.state.kafka_producer.start()

    await kafka_consumer.start()

    yield

    await app.state.kafka_producer.stop()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_profile_repo() -> ProfileRepository:
    return app.state.profile_repo

def get_s3_uploader() -> S3Uploader:
    return app.state.s3_uploader

def get_recommender() -> EmbeddingRecommender:
    return app.state.recsys

def get_kafka_producer() -> KafkaEventProducer:
    return app.state.kafka_producer

def get_clickhouse_logger() -> ClickHouseLogger:
    return app.state.clickhouse_logger

def get_cached_location_resolver() -> CachedLocationResolver:
    return app.state.cached_location_resolver

def get_swipe_cache() -> SwipeCache:
    return app.state.swipe_cache

class ProfileBase(BaseModel):
    user_id: int
    name: str
    gender: str
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    age: int
    interesting_gender: str
    about: str

    @model_validator(mode="after")
    def check_location(self) -> 'ProfileBase':
        if not self.city and (self.latitude is None or self.longitude is None):
            raise ValueError("Укажите либо город, либо координаты (широту и долготу).")
        return self

class MediaItem(BaseModel):
    type: str
    s3_key: str

class MediaList(BaseModel):
    profile_id: int
    media: List[MediaItem]

class ToggleActive(BaseModel):
    user_id: int
    is_active: bool

class UpdateField(BaseModel):
    user_id: int
    field_name: str
    value: str

class ProfileId(BaseModel):
    profile_id: int

class SwipeInput(BaseModel):
    from_user_id: int
    to_user_id: int
    action: str
    message: Optional[str] = None


@app.post("/profile/save")
async def save_profile(
    profile: ProfileBase,
    repo: ProfileRepository = Depends(get_profile_repo),
    producer: KafkaEventProducer = Depends(get_kafka_producer),
    recommender: EmbeddingRecommender = Depends(get_recommender),
    geocoder: CachedLocationResolver = Depends(get_cached_location_resolver)
):
    if not profile.city and (profile.latitude is None or profile.longitude is None):
        raise HTTPException(
            status_code=400,
            detail="Укажите либо город, либо координаты"
        )

    try:
        if profile.city and (profile.latitude is None or profile.longitude is None):
            coords = await geocoder.resolve(profile.city)
            if coords:
                profile.latitude, profile.longitude = coords
            else:
                await producer.send_event(KAFKA_GEO_TOPIC, {
                    'user_id': profile.user_id,
                    'city': profile.city,
                    'action': 'resolve_coordinates'
                })
                profile.latitude = None
                profile.longitude = None

        profile_id = await repo.save_profile(
            user_id=profile.user_id,
            name=profile.name,
            gender=profile.gender,
            city=profile.city,
            age=profile.age,
            interesting_gender=profile.interesting_gender,
            about=profile.about,
            latitude=profile.latitude,
            longitude=profile.longitude
        )

        if profile.latitude and profile.longitude:
            await recommender.update_user_embedding(profile.user_id)
        else:
            await producer.send_event(KAFKA_GEO_NOTIFICATIONS_TOPIC, {
                'user_id': profile.user_id,
                'status': 'pending_coordinates',
                'city': profile.city
            })

        return {"profile_id": profile_id}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Ошибка при сохранении профиля"
        )

@app.post("/profile/media/save")
async def save_media(data: MediaList, repo: ProfileRepository = Depends(get_profile_repo)):
    media = [(item.type, item.s3_key) for item in data.media]
    await repo.save_media(data.profile_id, media)
    return {"status": "ok"}

@app.get("/profile/by_user/{user_id}")
async def get_profile_by_user_id(user_id: int, repo: ProfileRepository = Depends(get_profile_repo)):
    row = await repo.get_profile_by_user_id(user_id)
    return dict(row) if row else None

@app.get("/profile/media/{profile_id}")
async def get_media_by_profile_id(profile_id: int, repo: ProfileRepository = Depends(get_profile_repo)):
    rows = await repo.get_media_by_profile_id(profile_id)
    return [dict(row) for row in rows]

@app.post("/profile/toggle_active")
async def toggle_active(data: ToggleActive, repo: ProfileRepository = Depends(get_profile_repo)):
    await repo.toggle_profile_active(data.user_id, data.is_active)
    return {"status": "ok"}

@app.post("/profile/update_field")
async def update_field(
    data: UpdateField, 
    repo: ProfileRepository = Depends(get_profile_repo), 
    producer: KafkaEventProducer = Depends(get_kafka_producer), 
    recommender: EmbeddingRecommender = Depends(get_recommender),
    geocoder: CachedLocationResolver = Depends(get_cached_location_resolver)
):
    try:
        if not data.user_id or not data.field_name:
            raise HTTPException(
                status_code=400,
                detail="user_id and field_name are required"
            )

        await repo.update_profile_field(data.user_id, data.field_name, data.value)

        if data.field_name == 'about':
            await recommender.update_user_embedding(data.user_id)

        elif data.field_name == 'city':
            try:
                await producer.send_event(KAFKA_GEO_NOTIFICATIONS_TOPIC, {
                    'user_id': data.user_id,
                    'status': 'processing',
                    'city': data.value,
                    'timestamp': datetime.utcnow().isoformat()
                })

                coords = await geocoder.resolve(data.value)
                if coords:
                    lat, lon = coords
                    await repo.update_profile_field(data.user_id, 'latitude', lat)
                    await repo.update_profile_field(data.user_id, 'longitude', lon)

                    await producer.send_event(KAFKA_GEO_TOPIC, {
                        'user_id': data.user_id,
                        'city': data.value,
                        'latitude': lat,
                        'longitude': lon,
                        'status': 'completed',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                else:
                    await producer.send_event(KAFKA_GEO_NOTIFICATIONS_TOPIC, {
                        'user_id': data.user_id,
                        'status': 'failed',
                        'reason': 'geocoding_failed',
                        'city': data.value,
                        'timestamp': datetime.utcnow().isoformat()
                    })

            except Exception as e:
                await producer.send_event(KAFKA_GEO_NOTIFICATIONS_TOPIC, {
                    'user_id': data.user_id,
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })

        return {"status": "ok"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update field: {str(e)}"
        )

@app.delete("/profile/media/delete")
async def delete_media(data: ProfileId, repo: ProfileRepository = Depends(get_profile_repo)):
    await repo.delete_media_by_profile_id(data.profile_id)
    return {"status": "deleted"}

@app.post("/s3/upload")
async def upload_file_to_s3(
    file: UploadFile = File(...),
    uploader: S3Uploader = Depends(get_s3_uploader)
):
    try:
        file_bytes = await file.read()
        byte_stream = BytesIO(file_bytes)
        key = await uploader.upload_file(byte_stream, file.filename)
        return {"key": key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/s3/url")
async def get_presigned_url(key: str, expiration: Optional[int] = 3600, uploader: S3Uploader = Depends(get_s3_uploader)):
    try:
        url = uploader.generate_presigned_url(key, expiration)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/s3/delete")
async def delete_file_from_s3(key: str = Form(...), uploader: S3Uploader = Depends(get_s3_uploader)):
    try:
        await uploader.delete_file_by_key(key)
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recsys/recommendations/{user_id}")
async def get_recommendations(user_id: int, count: int = 10, recommender: EmbeddingRecommender = Depends(get_recommender)):
    try:
        recommendations = await recommender.get_hybrid_recommendations(user_id=user_id, count=count)
        return {"recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/swipe/add")
async def add_swipe(
    swipe: SwipeInput,
    repo: ProfileRepository = Depends(get_profile_repo),
    producer: KafkaEventProducer = Depends(get_kafka_producer),
    logger: ClickHouseLogger = Depends(get_clickhouse_logger),
    swipe_cache: SwipeCache = Depends(get_swipe_cache)
):
    if swipe.action not in {"like", "dislike", "question"}:
        raise HTTPException(status_code=400, detail="Invalid swipe action")

    try:
        await repo.save_swipe(
            from_user_id=swipe.from_user_id,
            to_user_id=swipe.to_user_id,
            action=swipe.action,
            message=swipe.message
        )

        await swipe_cache.add_swipe(
            swipe.from_user_id, 
            swipe.to_user_id
        )

        from_profile = await repo.get_profile_by_user_id(swipe.from_user_id)
        to_profile = await repo.get_profile_by_user_id(swipe.to_user_id)

        logger.insert_swipe(
            from_user_id=swipe.from_user_id,
            to_user_id=swipe.to_user_id,
            action=swipe.action,
            from_city=from_profile['city'],
            to_city=to_profile['city'],
            from_gender=from_profile['gender'],
            to_gender=to_profile['gender'],
            from_age=from_profile['age'],
            to_age=to_profile['age'],
            message=swipe.message
        )

        if swipe.action in {"like", "question"}:
            await producer.send_event(KAFKA_SWIPES_TOPIC,{
                'from_user_id': swipe.from_user_id,
                'to_user_id': swipe.to_user_id,
                'action': swipe.action,
                'message': swipe.message
            })

        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
