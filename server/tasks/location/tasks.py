from infrastructure.messaging.celery.celery_app import celery_app
from infrastructure.messaging.celery.base_task import BaseTask
from contracts.kafka.events import LocationResolveResultEvent
from core.config import get_settings

settings = get_settings()

@celery_app.task(
    name="location.update_user_location",
    bind=True,
    base=BaseTask,
    queue='location',
    routing_key='location.update'
)
def update_user_location(self, user_id: int, city: str):
    try:
        coords = self.location_resolver.resolve(city)

        event = LocationResolveResultEvent(
            user_id=user_id,
            status="success" if coords else "failed",
            latitude=coords[0] if coords else None,
            longitude=coords[1] if coords else None
        )

        self.producer.send_event(settings.KAFKA_GEO_TOPIC, event.model_dump())
    except Exception as exc:
        raise self.retry(exc=exc)