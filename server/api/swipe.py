from fastapi import APIRouter, Depends, HTTPException

from database.ProfileRepository import ProfileRepository
from kafka_events.producer import KafkaEventProducer
from clickhouse.ClickHouseLogger import ClickHouseLogger
from cache.SwipeCache import SwipeCache
from core.dependecies import get_profile_repo, get_kafka_producer, get_clickhouse_logger, get_swipe_cache
from core.config import KAFKA_SWIPES_TOPIC
from models.swipe import SwipeInput

router = APIRouter()

@router.post("/add")
async def add_swipe(
    swipe: SwipeInput,
    repo: ProfileRepository = Depends(get_profile_repo),
    producer: KafkaEventProducer = Depends(get_kafka_producer),
    logger: ClickHouseLogger = Depends(get_clickhouse_logger),
    swipe_cache: SwipeCache = Depends(get_swipe_cache)
):
    if swipe.action not in {"like", "dislike", "question"}:
        raise HTTPException(status_code=400, detail="Invalid swipe action")

    try:
        await repo.save_swipe(
            from_user_id=swipe.from_user_id,
            to_user_id=swipe.to_user_id,
            action=swipe.action,
            message=swipe.message
        )

        await swipe_cache.add_swipe(
            swipe.from_user_id, 
            swipe.to_user_id
        )

        from_profile = await repo.get_profile_by_user_id(swipe.from_user_id)
        to_profile = await repo.get_profile_by_user_id(swipe.to_user_id)

        logger.insert_swipe(
            from_user_id=swipe.from_user_id,
            to_user_id=swipe.to_user_id,
            action=swipe.action,
            from_city=from_profile['city'],
            to_city=to_profile['city'],
            from_gender=from_profile['gender'],
            to_gender=to_profile['gender'],
            from_age=from_profile['age'],
            to_age=to_profile['age'],
            message=swipe.message
        )

        if swipe.action in {"like", "question"}:
            await producer.send_event(KAFKA_SWIPES_TOPIC,{
                'from_user_id': swipe.from_user_id,
                'to_user_id': swipe.to_user_id,
                'action': swipe.action,
                'message': swipe.message
            })

        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
