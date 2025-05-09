from fastapi import Header

async def get_user_id_from_headers(x_user_id: int = Header(..., alias="X-User-ID")):
    return x_user_id

async def get_username_from_headers(x_telegram_username: str = Header(..., alias="X-Telegram-Username")):
    return x_telegram_username
