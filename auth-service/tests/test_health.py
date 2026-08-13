import pytest
from src.routes.health import get_health

@pytest.mark.asyncio
async def test_get_health():
    res = await get_health()
    assert res['status'] == 'healthy'
