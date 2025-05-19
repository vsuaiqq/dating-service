from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator

from core.lifespan import lifespan
from core.config import get_settings
from shared.exceptions.exceptions import AppException
from shared.exceptions.error_handlers import http_exception_handler, app_exception_handler, unhandled_exception_handler, validation_exception_handler, rate_limit_handler
from api.v1.middlewares.logging_middleware import LoggingMiddleware
from api.v1.middlewares.auth_middleware import AuthMiddleware
from api.v1.routes.profile import router as profile_router
from api.v1.routes.recommendation import router as recommendation_router
from api.v1.routes.media import router as media_router
from api.v1.routes.swipe import router as swipe_router
from api.v1.meta.tags import tags_metadata

app = FastAPI(
    title="Dating Service API",
    description="This API provides endpoints for managing user profiles, recommendations, swipes, and media uploads.",
    version="1.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan
)

Instrumentator().instrument(app).expose(app)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthMiddleware)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(profile_router, prefix='/profile', tags=['Profiles'])
app.include_router(recommendation_router, prefix='/recsys', tags=['Recommendations'])
app.include_router(media_router, prefix='/media', tags=['Media'])
app.include_router(swipe_router, prefix='/swipe', tags=['Swipes'])
