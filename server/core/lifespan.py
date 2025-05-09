from fastapi import FastAPI
from contextlib import asynccontextmanager
from di.container import Container

@asynccontextmanager
async def lifespan(app: FastAPI):
    container = Container()
    container.wire(
        modules=[
            "api.v1.routers.profile",
            "api.v1.routers.media",
            "api.v1.routers.recommendation",
            "api.v1.routers.swipe"
        ]
    )
    
    app.container = container

    await container.init_resources()

    kafka = await container.kafka()
    await kafka.consumer.start()
    await kafka.producer.start()

    yield

    await kafka.producer.stop()
    await kafka.consumer.stop()

    await container.shutdown_resources()
