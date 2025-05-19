from infrastructure.messaging.celery.celery_app import celery_app
from infrastructure.messaging.celery.video_task import VideoValidationTask
from contracts.kafka.events import VideoValidationResultEvent
from core.config import get_settings

settings = get_settings()

@celery_app.task(
    name="video.validate_video",
    bind=True,
    base=VideoValidationTask,
    queue='video',
    routing_key='video.validate'
)
def validate_video(self: VideoValidationTask, user_id: int, file_bytes: bytes):
    try:
        event = VideoValidationResultEvent(
            user_id=user_id,
            is_human=self.video_validator.analyze_video_bytes(file_bytes)
        )

        self.producer.send_event(settings.KAFKA_VIDEO_TOPIC, event.model_dump())
    except Exception as exc:
        raise self.retry(exc=exc)
