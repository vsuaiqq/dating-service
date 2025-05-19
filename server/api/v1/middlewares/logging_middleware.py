import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from core.logger import logger

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        correlation_id = request.headers.get("X-Correlation-ID", request_id)

        request.state.request_id = request_id
        request.state.correlation_id = correlation_id

        start = time.time()
        logger.info(
            "Incoming request",
            extra={
                "request_id": request_id,
                "correlation_id": correlation_id,
                "method": request.method,
                "url": str(request.url),
            }
        )

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            logger.exception("Unhandled error", extra={"request_id": request_id, "correlation_id": correlation_id})
            raise exc

        duration = round((time.time() - start) * 1000, 2)
        logger.info(
            "Response sent",
            extra={
                "request_id": request_id,
                "correlation_id": correlation_id,
                "status_code": response.status_code,
                "duration_ms": duration
            }
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Correlation-ID"] = correlation_id

        return response
