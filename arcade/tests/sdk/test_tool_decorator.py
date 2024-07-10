import pytest
import asyncio
from arcade.sdk.tool import tool

@pytest.mark.asyncio
async def test_sync_function():
    """
    Ensures a sync function will run when decorated by @tool
    """
    @tool
    def sync_func(x, y):
        return x + y

    result = await sync_func(1, 2)
    assert result == 3

@pytest.mark.asyncio
async def test_async_function():
    """
    Ensures an async function will run when decorated by @tool
    """
    @tool
    async def async_func(x, y):
        await asyncio.sleep(0);
        return x + y

    result = await async_func(1, 2)
    assert result == 3