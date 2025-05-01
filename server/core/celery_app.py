from celery import Celery

from core.config import get_settings

settings = get_settings()
redis_url = settings.redis_url_celery

celery_app = Celery(
    __name__,
    broker=redis_url,
    backend=redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

celery_app.autodiscover_tasks([
    'tasks.geo',
    'tasks.video'
])
