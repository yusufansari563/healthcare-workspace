import pytest
import asyncio
from src.middleware.rate_limiter import RateLimiter

@pytest.mark.asyncio
async def test_rate_limiter_initialization():
    limiter = RateLimiter(max_requests=10, window_seconds=60)
    assert limiter.max_requests == 10
