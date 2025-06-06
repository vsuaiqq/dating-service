import asyncio
import json
from aiokafka import AIOKafkaConsumer

from core.logger import logger

class KafkaEventConsumer:
    def __init__(self, bootstrap_servers: str, topics: list, callback):
        self.topics = topics
        self.bootstrap_servers = bootstrap_servers
        self.callback = callback
        self._consumer: AIOKafkaConsumer | None = None

    async def start(self):
        self._consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=self.bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest'
        )
        await self._consumer.start()
        asyncio.create_task(self.consume_loop())
    
    async def stop(self):
        if self._consumer:
            await self._consumer.stop()

    async def consume_loop(self):
        async for msg in self._consumer:
            data = msg.value
            try:
                await self.callback(data)
            except Exception as e:
                logger.error(f"Invalid event: {e}")
