"""Tool for retrieving information about the currently authenticated user."""

from typing import Annotated, Dict

from arcade.context import ToolContext
from arcade.tool import Discord, tool
from arcade_discord.utils import make_discord_request


@tool(
    requires_auth=Discord(
        scopes=["identify"],
    )
)
async def get_current_user(
    context: ToolContext,
) -> Annotated[Dict, "Information about the authenticated user"]:
    """
    Get information about the currently authenticated user.

    This tool retrieves detailed information about the user associated
    with the current authentication token, including username, ID,
    avatar, and other profile details.

    Example:
        ```python
        get_current_user()
        ```
    """
    # Send the request to Discord API
    response = make_discord_request(
        context=context,
        method="GET",
        endpoint="/users/@me",
        context_message="get current user information",
    )

    # Return in a user-friendly format
    return {
        "id": response.get("id"),
        "username": response.get("username"),
        "discriminator": response.get("discriminator"),
        "global_name": response.get("global_name"),
        "avatar": response.get("avatar"),
        "bot": response.get("bot", False),
        "email": response.get("email"),
        "verified": response.get("verified"),
        "flags": response.get("flags"),
        "premium_type": response.get("premium_type"),
        "accent_color": response.get("accent_color"),
        "locale": response.get("locale"),
    }
