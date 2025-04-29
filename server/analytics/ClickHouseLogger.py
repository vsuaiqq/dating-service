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
        from_city: str,
        to_city: str,
        from_gender: Literal['male', 'female'],
        to_gender: Literal['male', 'female'],
        from_age: int,
        to_age: int,
        message: Optional[str] = None,
    ):
        try:
            created_at = datetime.utcnow()

            self.client.execute(
                """
                INSERT INTO dating_bot.user_swipes (
                    from_user_id, to_user_id, action, message, created_at, 
                    from_city, to_city, from_gender, to_gender, from_age, to_age
                ) VALUES
                """,
                [[
                    from_user_id, to_user_id, action, message, created_at, 
                    from_city, to_city, from_gender, to_gender, from_age, to_age
                ]]
            )
        except Exception as e:
            logging.error(f"ClickHouse insert error: {e}")
            raise
