"""
Rate Limiter Middleware
"""
import time
from fastapi import Request, HTTPException, status

class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}

    async def __call__(self, request: Request):
        client_ip = request.client.host if request.client else '127.0.0.1'
        now = time.time()
        user_reqs = [t for t in self.requests.get(client_ip, []) if now - t < self.window_seconds]
        if len(user_reqs) >= self.max_requests:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail='Rate limit exceeded')
        user_reqs.append(now)
        self.requests[client_ip] = user_reqs
