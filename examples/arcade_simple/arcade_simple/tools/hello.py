from typing import Annotated
from arcade.sdk.tool import tool


@tool
async def hello(
    name: Annotated[str, "The greeting to say after 'hello'"] = "World",
) -> str:
    """Return a greeting."""
    return f"Hello, {name}!"
