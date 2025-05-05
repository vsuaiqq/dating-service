from clickhouse_driver import Client
from datetime import datetime
from typing import Optional, Literal
import logging

class ClickHouseLogger:
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str
    ):
        self.client = Client(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )

    def insert_swipe(
            self,
            from_user_id: int,
            to_user_id: int,
            action: Literal['like', 'dislike', 'question'],
            from_city: Optional[str] = None,
            to_city: Optional[str] = None,
            from_gender: Optional[Literal['male', 'female']] = None,
            to_gender: Optional[Literal['male', 'female']] = None,
            from_age: Optional[int] = None,
            to_age: Optional[int] = None,
            message: Optional[str] = None,
    ):
        try:
            created_at = datetime.utcnow()

            data = [
                from_user_id,
                to_user_id,
                action,
                message or '',
                created_at,
                from_city or 'unknown',
                to_city or 'unknown',
                from_gender or 'unknown',
                to_gender or 'unknown',
                from_age or 0,
                to_age or 0
            ]

            self.client.execute(
                """
                INSERT INTO dating_bot.user_swipes (
                    from_user_id, to_user_id, action, message, created_at, 
                    from_city, to_city, from_gender, to_gender, from_age, to_age
                ) VALUES
                """,
                [data]
            )
        except Exception as e:
            logging.error(f"ClickHouse insert error: {e}", exc_info=True)
            raise
