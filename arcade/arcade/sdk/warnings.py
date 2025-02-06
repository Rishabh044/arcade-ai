import warnings
from functools import wraps


def deprecated(reason: str, stacklevel: int = 3):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__} is deprecated: {reason}",
                DeprecationWarning,
                stacklevel=stacklevel,
            )
            return await func(*args, **kwargs)

        return wrapper

    return decorator
