import re
from collections.abc import Iterable
from typing import Any, Optional, TypeVar

T = TypeVar("T")


def first_or_none(_type: type[T], iterable: Iterable[Any]) -> Optional[T]:
    """
    Returns the first item in the iterable that is an instance of the given type, or None if no such item is found.
    """
    for item in iterable:
        if isinstance(item, _type):
            return item
    return None


# Utility function to convert CamelCase to snake_case
def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def snake_to_camel(name):
    return "".join(x.capitalize() or "_" for x in name.split("_"))
