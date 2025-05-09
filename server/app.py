from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi.errors import RateLimitExceeded

from core.lifespan import lifespan
from core.config import get_settings
from shared.exceptions.exceptions import AppException
from shared.exceptions.error_handlers import http_exception_handler, app_exception_handler, unhandled_exception_handler, validation_exception_handler, rate_limit_handler
from api.v1.middlewares.token_verification import TokenVerificationMiddleware
from api.v1.routers.profile import router as profile_router
from api.v1.routers.recommendation import router as recommendation_router
from api.v1.routers.media import router as media_router
from api.v1.routers.swipe import router as swipe_router
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(lifespan=lifespan)

Instrumentator().instrument(app).expose(app)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TokenVerificationMiddleware)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(profile_router, prefix='/profile', tags=['Profiles'])
app.include_router(recommendation_router, prefix='/recsys', tags=['Recommendations'])
app.include_router(media_router, prefix='/media', tags=['Media'])
app.include_router(swipe_router, prefix='/swipe', tags=['Swipes'])
