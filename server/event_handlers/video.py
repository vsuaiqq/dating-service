from core.config import Settings
from infrastructure.messaging.kafka.producer import KafkaEventProducer
from contracts.kafka.events import VideoValidationResultEvent

async def on_video_validation_event(
    event: VideoValidationResultEvent,
    producer: KafkaEventProducer,
    settings: Settings,
):
    await producer.send_event(settings.KAFKA_VIDEO_NOTIFICATIONS_TOPIC, event.model_dump())
