from core.config import get_settings
from services.video.video_validator import VideoValidator
from infrastructure.messaging.celery.celery_app import celery_app
from infrastructure.messaging.kafka.producer_sync import KafkaEventProducerSync
from contracts.kafka.events import VideoValidationResultEvent

settings = get_settings()

@celery_app.task(name="video.validate_video", bind=True)
def validate_video(self, user_id: int, file_bytes: bytes):
    try:
        producer = KafkaEventProducerSync(settings.kafka_bootstrap_servers)

        producer.start()

        event = VideoValidationResultEvent(
            user_id=user_id,
            is_human=VideoValidator(frame_skip=5, face_threshold=0.5).analyze_video_bytes(file_bytes)
        )
        
        producer.send_event(settings.KAFKA_VIDEO_TOPIC, event.model_dump())

        producer.stop()
    except Exception as exc:
        raise self.retry(exc=exc)
 