from aiokafka import AIOKafkaConsumer
import asyncio
import json

class KafkaEventConsumer:
    def __init__(self, bootstrap_servers: str, topic: str, callback):
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self.callback = callback
        self._consumer: AIOKafkaConsumer | None = None

    async def start(self):
        self._consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest'
        )
        await self._consumer.start()
        asyncio.create_task(self.consume_loop())

    async def consume_loop(self):
        async for msg in self._consumer:
            data = msg.value
            try:
                await self.callback(data)
            except Exception as e:
                print(f"Invalid event: {e}")
