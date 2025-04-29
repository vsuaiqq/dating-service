from fastapi import APIRouter, Depends, HTTPException

from database.ProfileRepository import ProfileRepository
from services.recsys.recsys import EmbeddingRecommender
from kafka_events.producer import KafkaEventProducer
from cache.RecommendationCache import RecommendationCache
from core.dependecies import get_recommender, get_profile_repo, get_kafka_producer, get_recommendation_cache
from core.config import get_settings
from models.profile import ProfileBase, ProfileId, ToggleActive
from models.media import MediaList
from models.fields import UpdateField
from tasks.geo.tasks import update_user_location

router = APIRouter()

settings = get_settings()

@router.post("/save")
async def save_profile(
    profile: ProfileBase,
    repo: ProfileRepository = Depends(get_profile_repo),
    producer: KafkaEventProducer = Depends(get_kafka_producer),
    recommender: EmbeddingRecommender = Depends(get_recommender),
):
    try:
        if profile.latitude is None or profile.longitude is None:
            await producer.send_event(settings.KAFKA_GEO_NOTIFICATIONS_TOPIC, {
                'user_id': profile.user_id,
                'status': 'waited'
            })
            update_user_location.delay(
                user_id=profile.user_id,
                city=profile.city
            )
        
        fallback_coordinates = (55.625578, 37.6063916)

        profile_id = await repo.save_profile(
            profile.user_id,
            profile.name,
            profile.gender,
            profile.city,
            profile.age,
            profile.interesting_gender,
            profile.about,
            profile.latitude or fallback_coordinates[0],
            profile.longitude or fallback_coordinates[1]
        )

        await recommender.update_user_embedding(profile.user_id)

        return {"profile_id": profile_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/media/save")
async def save_media(data: MediaList, repo: ProfileRepository = Depends(get_profile_repo)):
    try:
        media = [(item.type, item.s3_key) for item in data.media]
        await repo.save_media(data.profile_id, media)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by_user/{user_id}")
async def get_profile_by_user_id(user_id: int, repo: ProfileRepository = Depends(get_profile_repo)):
    try:
        row = await repo.get_profile_by_user_id(user_id)
        return dict(row) if row else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/media/{profile_id}")
async def get_media_by_profile_id(profile_id: int, repo: ProfileRepository = Depends(get_profile_repo)):
    try:
        rows = await repo.get_media_by_profile_id(profile_id)
        return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/toggle_active")
async def toggle_active(data: ToggleActive, repo: ProfileRepository = Depends(get_profile_repo)):
    try:
        await repo.toggle_profile_active(data.user_id, data.is_active)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update_field")
async def update_field(
    data: UpdateField, 
    repo: ProfileRepository = Depends(get_profile_repo), 
    producer: KafkaEventProducer = Depends(get_kafka_producer), 
    recommender: EmbeddingRecommender = Depends(get_recommender),
    cache: RecommendationCache = Depends(get_recommendation_cache)
):
    try:
        if data.field_name != 'coordinates':
            await repo.update_profile_field(data.user_id, data.field_name, data.value)

        if data.field_name == 'about':
            await recommender.update_user_embedding(data.user_id)

        if data.field_name == 'city':
            await producer.send_event(settings.KAFKA_GEO_NOTIFICATIONS_TOPIC, {
                'user_id': data.user_id,
                'status': 'waited'
            })
            update_user_location.delay(
                user_id=data.user_id,
                city=data.value
            )

        if data.field_name == 'coordinates':
            await repo.update_coordinates(data.user_id, data.value.latitude, data.value.longitude)
            await repo.reset_city(data.user_id)
            await cache.clear(data.user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/media/delete")
async def delete_media(data: ProfileId, repo: ProfileRepository = Depends(get_profile_repo)):
    try:
        await repo.delete_media_by_profile_id(data.profile_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
