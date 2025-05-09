from fastapi import Header

from shared.exceptions.exceptions import TokenException

async def get_user_id_from_headers(x_user_id: int = Header(..., alias="X-User-ID")):
    return x_user_id

async def get_username_from_headers(x_telegram_username: str = Header(..., alias="X-Telegram-Username")):        
    return x_telegram_username

async def get_token_from_headers(authorization: str = Header(..., alias="Authorization")):
    if authorization is None or not authorization.startswith("Bearer "):
        raise TokenException()
    
    token = authorization[7:]
    
    return token
