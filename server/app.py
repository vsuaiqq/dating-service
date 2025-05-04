from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.lifespan import lifespan
from core.config import get_settings
from api.profile import router as profile_router
from api.recsys import router as recsys_router
from api.media import router as media_router
from api.swipe import router as swipe_router

app = FastAPI(lifespan=lifespan)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile_router, prefix='/profile', tags=['Profile'])
app.include_router(recsys_router, prefix='/recsys', tags=['Recommendations'])
app.include_router(media_router, prefix='/media', tags=['Media'])
app.include_router(swipe_router, prefix='/swipe', tags=['Swipes'])
