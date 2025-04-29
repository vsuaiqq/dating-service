from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.lifespan import lifespan
from core.config import ORIGINS
from api.profile import router as profile_router
from api.recsys import router as recsys_router
from api.s3 import router as s3_router
from api.swipe import router as swipe_router

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile_router, prefix='/profile')
app.include_router(recsys_router, prefix='/recsys')
app.include_router(s3_router, prefix='/s3')
app.include_router(swipe_router, prefix='/swipe')
