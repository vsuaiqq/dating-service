from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from fastapi import UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from io import BytesIO

from postgres.connection import create_db_pool
from postgres.ProfileRepository import ProfileRepository
from s3.S3Uploader import S3Uploader
from recsys.recsys import EmbeddingRecommender
from kafka_events.producer import KafkaEventProducer

from config import (
    S3_BUCKET_NAME, S3_REGION_NAME, S3_ACCESS_KEY_ID,
    S3_SECRET_ACCESS_KEY, S3_ENDPOINT_URL
)

app = FastAPI()

ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    pool = await create_db_pool()
    profile_repo = ProfileRepository(pool)

    app.state.pool = pool
    app.state.profile_repo = profile_repo
    app.state.s3_uploader = S3Uploader(
        bucket_name=S3_BUCKET_NAME,
        region=S3_REGION_NAME,
        access_key=S3_ACCESS_KEY_ID,
        secret_key=S3_SECRET_ACCESS_KEY,
        endpoint_url=S3_ENDPOINT_URL
    )
    app.state.recsys = EmbeddingRecommender(
        profile_repo=profile_repo
    )
    app.state.kafka_producer = KafkaEventProducer("localhost:9092", "swipes")

    await app.state.kafka_producer.start()

@app.on_event("shutdown")
async def shutdown_event():
    await app.state.kafka_producer.stop()

def get_profile_repo() -> ProfileRepository:
    return app.state.profile_repo

def get_s3_uploader() -> S3Uploader:
    return app.state.s3_uploader

def get_recommender() -> EmbeddingRecommender:
    return app.state.recsys

def get_kafka_producer() -> KafkaEventProducer:
    return app.state.kafka_producer

class ProfileBase(BaseModel):
    user_id: int
    name: str
    gender: str
    city: str
    age: int
    interesting_gender: str
    about: str

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
async def save_profile(profile: ProfileBase, repo: ProfileRepository = Depends(get_profile_repo), recommender: EmbeddingRecommender = Depends(get_recommender)):
    profile_id = await repo.save_profile(
        profile.user_id,
        profile.name,
        profile.gender,
        profile.city,
        profile.age,
        profile.interesting_gender,
        profile.about
    )

    await recommender.update_user_embedding(profile.user_id)

    return {"profile_id": profile_id}

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
async def update_field(data: UpdateField, repo: ProfileRepository = Depends(get_profile_repo), recommender: EmbeddingRecommender = Depends(get_recommender)):
    await repo.update_profile_field(data.user_id, data.field_name, data.value)

    if data.field_name == 'about':
        await recommender.update_user_embedding(data.user_id)

    return {"status": "ok"}

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
    kafka: KafkaEventProducer = Depends(get_kafka_producer)
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

        if swipe.action in {"like", "question"}:
            await kafka.send_event({
                'from_user_id': swipe.from_user_id,
                'to_user_id': swipe.to_user_id,
                'action': swipe.action,
                'message': swipe.message
            })

        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
