from infrastructure.messaging.celery.celery_app import celery_app
from infrastructure.messaging.celery.base_task import BaseTask
from contracts.kafka.events import VideoValidationResultEvent
from services.video.video_validator import VideoValidator
from core.config import get_settings

settings = get_settings()


@celery_app.task(
    name="video.validate_video",
    bind=True,
    base=BaseTask,
    queue='video',
    routing_key='video.validate'
)
def validate_video(self, user_id: int, file_bytes: bytes):
    try:
        event = VideoValidationResultEvent(
            user_id=user_id,
            is_human=VideoValidator(frame_skip=5, face_threshold=0.5).analyze_video_bytes(file_bytes)
        )

        self.producer.send_event(settings.KAFKA_VIDEO_TOPIC, event.model_dump())
    except Exception as exc:
        raise self.retry(exc=exc)