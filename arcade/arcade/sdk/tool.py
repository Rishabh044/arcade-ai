import os
from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


class Description:
    def __init__(self, description: str):
        self.description = description

    def __str__(self):
        return self.description


def tool(
    func: Callable | None = None, name: str | None = None, description: str | None = None
) -> Callable:
    def decorator(func: Callable) -> Callable:
        func.__tool_name__ = name or getattr(func, "__name__", "unknown")
        func.__tool_description__ = description or func.__doc__

        return func

    if func:  # This means the decorator is used without parameters
        return decorator(func)
    return decorator


def get_secret(name: str, default: Optional[Any] = None) -> str:
    secret = os.getenv(name)
    if secret is None:
        if default is not None:
            return default
        raise ValueError(f"Secret {name} is not set.")
    return secret
