from aiokafka import AIOKafkaProducer
import json

class KafkaEventProducer:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self._producer: AIOKafkaProducer | None = None

    async def start(self):
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        await self._producer.start()

    async def stop(self):
        if self._producer:
            await self._producer.stop()

    async def send_event(self, topic: str, event: dict):
        if not self._producer:
            raise RuntimeError("Kafka producer not initialized")
        await self._producer.send_and_wait(topic, event)
