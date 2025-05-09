from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import get_settings
from api.v1.dependecies.headers import get_token_from_headers
from shared.exceptions.exceptions import TokenException

settings = get_settings()

class TokenVerificationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)
        
        token = await get_token_from_headers(request.headers.get('Authorization'))
        
        if token != settings.API_SECRET_KEY:
            raise TokenException()
        
        response = await call_next(request)
        return response
