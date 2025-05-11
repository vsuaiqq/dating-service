from celery import Celery
from kombu import Exchange, Queue

from core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "worker",
    broker=settings.redis_url_celery,
    backend=settings.redis_url_celery,
    include=[
        "tasks.location",
        "tasks.video",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    broker_transport_options={"visibility_timeout": 3600},

    task_default_retry_delay=10,
    task_annotations={
        '*': {
            'max_retries': 5,
            'default_retry_delay': 10,
        }
    },

    task_queues=[
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("location", Exchange("location"), routing_key="location.#"),
        Queue("video", Exchange("video"), routing_key="video.#"),
    ],
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
)

celery_app.autodiscover_tasks([
    "tasks.location",
    "tasks.video",
])
