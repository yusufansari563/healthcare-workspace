# Request Logging Middleware for auth-service
import logging
import time
from fastapi import Request

logger = logging.getLogger("auth-service.middleware")

class RequestLoggerMiddleware:
    async def __call__(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        logger.info(
            "[%s] %s - Status: %s (%.3fs)",
            request.method,
            request.url.path,
            response.status_code,
            duration,
        )
        return response