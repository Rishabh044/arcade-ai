from typing import Annotated, TypeVar, _AnnotatedAlias, Type, Callable, Any, Optional
import functools
import os
import asyncio

T = TypeVar('T')

class Description:
    def __init__(self, description: str):
        self.description = description

    def __str__(self):
        return self.description

def Param(type_: Type[T], description: str) -> Annotated[T, Description]:
    return Annotated[type_, Description(description)]

def tool(func: Callable) -> Callable:
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