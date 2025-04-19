from fastapi import FastAPI, Depends, HTTPException
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

def get_profile_repo() -> ProfileRepository:
    return app.state.profile_repo

# Pydantic модели
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

# Эндпоинты

@app.post("/profile/save")
async def save_profile(profile: ProfileBase, repo: ProfileRepository = Depends(get_profile_repo)):
    profile_id = await repo.save_profile(
        profile.user_id,
        profile.name,
        profile.gender,
        profile.city,
        profile.age,
        profile.interesting_gender,
        profile.about
    )
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
async def update_field(data: UpdateField, repo: ProfileRepository = Depends(get_profile_repo)):
    await repo.update_profile_field(data.user_id, data.field_name, data.value)
    return {"status": "ok"}

@app.delete("/profile/media/delete")
async def delete_media(data: ProfileId, repo: ProfileRepository = Depends(get_profile_repo)):
    await repo.delete_media_by_profile_id(data.profile_id)
    return {"status": "deleted"}

def get_s3_uploader() -> S3Uploader:
    return app.state.s3_uploader

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