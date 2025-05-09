from core.config import get_settings
from video.video_validator import VideoValidator
from infrastructure.messaging.celery.app import celery_app
from infrastructure.messaging.kafka.producer_sync import KafkaEventProducerSync
from contracts.kafka.events import VideoValidationResultEvent

settings = get_settings()

@celery_app.task(name="validate_video")
def validate_video(user_id: int, file_bytes: bytes):
    producer = KafkaEventProducerSync(settings.kafka_bootstrap_servers)

    producer.start()

    event = VideoValidationResultEvent(
        user_id=user_id,
        is_human=VideoValidator(frame_skip=5, face_threshold=0.5).analyze_video_bytes(file_bytes)
    )
    
    producer.send_event(settings.KAFKA_VIDEO_TOPIC, event.model_dump())

    producer.stop()
 