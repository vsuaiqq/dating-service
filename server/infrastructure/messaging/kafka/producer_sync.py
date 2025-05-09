import asyncio
import json
from aiokafka import AIOKafkaProducer

class KafkaEventProducerSync:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self._producer = None
        self._loop = None

    def start(self):
        if not self._loop:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        self._producer = self._loop.run_until_complete(self._init_producer())

    def stop(self):
        if self._producer:
            self._loop.run_until_complete(self._producer.stop())
        if self._loop:
            self._loop.run_until_complete(self._loop.shutdown_asyncgens())
            self._loop.close()
            self._loop = None

    def _run_coroutine(self, coro):
        return self._loop.run_until_complete(coro)

    async def _init_producer(self):
        producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        await producer.start()
        return producer

    def send_event(self, topic: str, event: dict):
        if not self._producer:
            raise RuntimeError("Kafka producer is not started")
        self._run_coroutine(self._producer.send_and_wait(topic, event))
