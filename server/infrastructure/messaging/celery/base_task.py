from celery import Task
import threading
import atexit

from core.config import get_settings
from infrastructure.messaging.kafka.producer_sync import KafkaEventProducerSync

settings = get_settings()

class BaseTask(Task):
    abstract = True

class KafkaTask(BaseTask):
    abstract = True

    _producer: KafkaEventProducerSync = None
    _lock = threading.Lock()

    @classmethod
    def _init_producer(cls):
        with cls._lock:
            if cls._producer is None:
                cls._producer = KafkaEventProducerSync(settings.kafka_bootstrap_servers)
                cls._producer.start()
                atexit.register(cls._shutdown_producer)

    @classmethod
    def _shutdown_producer(cls):
        if cls._producer:
            cls._producer.stop()
            cls._producer = None

    @property
    def producer(self) -> KafkaEventProducerSync:
        if self._producer is None:
            self._init_producer()
        return self._producer
