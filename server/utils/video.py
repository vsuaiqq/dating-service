from kafka_events.producer import KafkaEventProducer
from core.config import get_settings
from models.kafka.events import VideoValidationResultEvent

settings = get_settings()

async def on_video_validation_event(
    producer: KafkaEventProducer,
    event: VideoValidationResultEvent
):
    await producer.send_event(settings.KAFKA_VIDEO_NOTIFICATIONS_TOPIC, event.model_dump())
