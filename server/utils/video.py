from kafka_events.producer import KafkaEventProducer
from core.config import get_settings

settings = get_settings()

async def on_video_validation_event(
    producer: KafkaEventProducer,
    event: dict
):
    try:
        await producer.send_event(settings.KAFKA_GEO_NOTIFICATIONS_TOPIC, event)
    except Exception:
        await producer.send_event(settings.KAFKA_GEO_NOTIFICATIONS_TOPIC, {
            'user_id': event["user_id"],
            'is_human': False
        })
