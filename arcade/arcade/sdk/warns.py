import warnings
from functools import wraps
from typing import Any, Callable


def deprecated(reason: str, stacklevel: int = 3) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(
                f"{func.__name__} is deprecated: {reason}",
                DeprecationWarning,
                stacklevel=stacklevel,
            )
            return await func(*args, **kwargs)

        return wrapper

    return decorator
