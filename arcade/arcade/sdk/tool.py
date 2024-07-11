import asyncio
import functools
import os
from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


class Description:
    def __init__(self, description: str):
        self.description = description

    def __str__(self):
        return self.description


def tool(func: Callable, name: str | None = None, description: str | None = None) -> Callable:
    func.__tool_name__ = name or getattr(func, "__name__", "unknown")
    func.__tool_description__ = description or func.__doc__

    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            loop = asyncio.get_running_loop()
            partial_func = functools.partial(func, *args, **kwargs)
            return await loop.run_in_executor(None, partial_func)

    return wrapper


def get_secret(name: str, default: Optional[Any] = None) -> str:
    secret = os.getenv(name)
    if secret is None:
        if default is not None:
            return default
        raise ValueError(f"Secret {name} is not set.")
    return secret
