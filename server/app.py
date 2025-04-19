from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from fastapi import UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from io import BytesIO

from db.connection import create_db_pool
from db.ProfileRepository import ProfileRepository
from s3.S3Uploader import S3Uploader
from config import (
    S3_BUCKET_NAME, S3_REGION_NAME, S3_ACCESS_KEY_ID,
    S3_SECRET_ACCESS_KEY, S3_ENDPOINT_URL
)
from recsys.recsys import EmbeddingRecommender

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
    app.state.pool = pool
    app.state.profile_repo = ProfileRepository(pool)
    app.state.s3_uploader = S3Uploader(
        bucket_name=S3_BUCKET_NAME,
        region=S3_REGION_NAME,
        access_key=S3_ACCESS_KEY_ID,
        secret_key=S3_SECRET_ACCESS_KEY,
        endpoint_url=S3_ENDPOINT_URL
    )
    app.state.recsys = EmbeddingRecommender(pool)

def get_profile_repo() -> ProfileRepository:
    return app.state.profile_repo

def get_recsys() -> EmbeddingRecommender:
    return app.state.recsys

def get_s3_uploader() -> S3Uploader:
    return app.state.s3_uploader


# Profile pydantic
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

# RecSys pydantic
class RecommendationItem(BaseModel):
    user_id: int
    name: str
    gender: str
    city: str
    age: int
    interesting_gender: str
    about: str
    similarity: Optional[float] = None
    photos: Optional[List[str]] = None

class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationItem]

class RecommendationParams(BaseModel):
    user_id: int
    count: Optional[int] = 10

# S3 pydantic
class S3UploadResponse(BaseModel):
    key: str
    url: str
    content_type: str

class S3BulkDeleteRequest(BaseModel):
    keys: List[str]

class UserPhotoUpdate(BaseModel):
    user_id: int
    photo_key: str
    is_main: bool

# Эндпоинты

@app.post("/profile/save")
async def save_profile(
    profile: ProfileBase,
    background_tasks: BackgroundTasks, 
    repo: ProfileRepository = Depends(get_profile_repo),
    recsys: EmbeddingRecommender = Depends(get_recsys)
):
    profile_id = await repo.save_profile(
        profile.user_id,
        profile.name,
        profile.gender,
        profile.city,
        profile.age,
        profile.interesting_gender,
        profile.about
    )
    
    background_tasks.add_task(recsys.update_user_embedding, profile.user_id)
    return {"profile_id": profile_id}

@app.post("/profile/media/save")
async def save_media(data: MediaList, repo: ProfileRepository = Depends(get_profile_repo)):
    media = [(item.type, item.s3_key) for item in data.media]
    await repo.save_media(data.profile_id, media)
    return {"status": "ok"}

@app.get("/profile/by_user/{user_id}")
async def get_profile_by_user_id(
    user_id: int, 
    repo: ProfileRepository = Depends(get_profile_repo),
    recsys: EmbeddingRecommender = Depends(get_recsys)
):
    """Получение профиля с проверкой актуальности эмбеддингов"""
    profile = await repo.get_profile_by_user_id(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile_dict = dict(profile)
    
    if not profile_dict.get('description_embedding'):
        await recsys.update_user_embedding(user_id)
    
    return profile_dict

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
    background_tasks: BackgroundTasks,
    repo: ProfileRepository = Depends(get_profile_repo),
    recsys: EmbeddingRecommender = Depends(get_recsys)
):
    """Обновление поля профиля с обработкой особых случаев"""
    await repo.update_profile_field(data.user_id, data.field_name, data.value)
    
    # Если обновлено поле "about", обновляем эмбеддинг
    if data.field_name == 'about':
        background_tasks.add_task(recsys.update_user_embedding, data.user_id)
    
    return {"status": "updated"}

@app.delete("/profile/media/delete")
async def delete_media(data: ProfileId, repo: ProfileRepository = Depends(get_profile_repo)):
    await repo.delete_media_by_profile_id(data.profile_id)
    return {"status": "deleted"}

# Эндпоинты рекомендательной системы
@app.post("/recommendations/get")
async def get_recommendations(
    params: RecommendationParams,
    recsys: EmbeddingRecommender = Depends(get_recsys),
    repo: ProfileRepository = Depends(get_profile_repo),
    s3: S3Uploader = Depends(get_s3_uploader)
):
    """Получение персонализированных рекомендаций"""
    try:
        recommendations = await recsys.get_recommendations(
            params.user_id,
            count=params.count
        )
        
        if not recommendations:
            return {"recommendations": []}
        
        enriched_recommendations = []
        for rec in recommendations:
            photos = await repo.get_media_by_profile_id(rec['id'])
            photo_urls = [
                s3.generate_presigned_url(photo['s3_key'], 3600)
                for photo in photos
                if photo['type'] == 'photo'
            ][:3] 
            
            enriched_rec = {
                **rec,
                "photos": photo_urls
            }
            enriched_recommendations.append(enriched_rec)
        
        return {"recommendations": enriched_recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error getting recommendations")

@app.post("/recommendations/update_embedding/{user_id}")
async def update_embedding(
    user_id: int,
    recsys: EmbeddingRecommender = Depends(get_recsys)
):
    """Принудительное обновление эмбеддинга пользователя"""
    try:
        success = await recsys.update_user_embedding(user_id)
        if not success:
            raise HTTPException(status_code=400, detail="No about text to generate embedding")
        return {"status": "embedding updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error updating embedding")

# Эндпоинты S3
@app.post("/s3/upload", response_model=S3UploadResponse)
async def upload_file_to_s3(
    file: UploadFile = File(...),
    uploader: S3Uploader = Depends(get_s3_uploader),
    repo: ProfileRepository = Depends(get_profile_repo)
):
    """Загрузка файла в S3 с автоматическим созданием записи в БД"""
    try:
        file_bytes = await file.read()
        file_io = io.BytesIO(file_bytes)
        
        key = await uploader.upload_file(file_io, file.filename)
        content_type = uploader._guess_content_type(file.filename)
        
        url = uploader.generate_presigned_url(key, expiration=3600)
        
        return {
            "key": key,
            "url": url,
            "content_type": content_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        file_io.close()

@app.post("/s3/upload-user-photo", response_model=S3UploadResponse)
async def upload_user_photo(
    user_id: int = Form(...),
    is_main: bool = Form(False),
    file: UploadFile = File(...),
    uploader: S3Uploader = Depends(get_s3_uploader),
    repo: ProfileRepository = Depends(get_profile_repo)
):
    """Загрузка фото пользователя с привязкой к профилю"""
    try:
        # Проверяем существование пользователя
        user = await repo.get_profile_by_user_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Загружаем фото
        file_bytes = await file.read()
        file_io = io.BytesIO(file_bytes)
        key = await uploader.upload_file(file_io, file.filename)
        
        # Если это главное фото, сбрасываем флаги у других фото
        if is_main:
            await repo.set_main_photo(key, user_id)
        else:
            await repo.save_media(user_id, key, is_main)
        
        # Генерируем URL
        url = uploader.generate_presigned_url(key)
        
        return {
            "key": key,
            "url": url,
            "content_type": uploader._guess_content_type(file.filename)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        file_io.close()

@app.post("/s3/url/{key}", response_model=str)
async def get_presigned_url(
    key: str, 
    expiration: Optional[int] = 3600, 
    uploader: S3Uploader = Depends(get_s3_uploader)
):
    """Получение временной ссылки на файл"""
    try:
        return uploader.generate_presigned_url(key, expiration)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/s3/delete/{key}")
async def delete_file_from_s3(
    key: str, 
    uploader: S3Uploader = Depends(get_s3_uploader),
    repo: ProfileRepository = Depends(get_profile_repo)
):
    """Удаление файла из S3 и связанных записей из БД"""
    try:
        await repo.delete_media_by_key(key)
        
        await uploader.delete_file_by_key(key)
        
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/s3/bulk-delete")
async def bulk_delete_files(
    request: S3BulkDeleteRequest,
    uploader: S3Uploader = Depends(get_s3_uploader),
    repo: ProfileRepository = Depends(get_profile_repo)
):
    """Массовое удаление файлов"""
    try:
        # Удаляем записи из БД
        await repo.bulk_delete_media(request.keys)
        
        # Удаляем файлы из S3
        await uploader.delete_files(request.keys)
        
        return {"status": "deleted", "count": len(request.keys)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/s3/update-user-photo")
async def update_user_photo(
    data: UserPhotoUpdate,
    uploader: S3Uploader = Depends(get_s3_uploader),
    repo: ProfileRepository = Depends(get_profile_repo)
):
    """Обновление фото пользователя"""
    try:
        if data.is_main:
            await repo.set_main_photo(data.photo_key, data.user_id)
        else:
            await repo.update_photo(data.photo_key, data.user_id, is_main=False)
            
        return {"status": "updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/s3/user-photos/{user_id}")
async def get_user_photos(
    user_id: int,
    repo: ProfileRepository = Depends(get_profile_repo),
    uploader: S3Uploader = Depends(get_s3_uploader)
):
    """Получение всех фото пользователя с временными ссылками"""
    try:
        photos = await repo.get_user_photos(user_id)
        return [{
            "id": photo["id"],
            "url": uploader.generate_presigned_url(photo["file_id"]),
            "is_main": photo["is_main"],
            "uploaded_at": photo["uploaded_at"]
        } for photo in photos]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))