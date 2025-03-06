"""Tool for creating Discord webhooks."""

from typing import Annotated, Dict, Optional

from arcade.context import ToolContext
from arcade.tool import Discord, tool
from arcade_discord.exceptions import DiscordValidationError
from arcade_discord.utils import WEBHOOK_SCOPES, make_discord_request


@tool(
    requires_auth=Discord(
        scopes=WEBHOOK_SCOPES,
    )
)
async def create_webhook(
    context: ToolContext,
    channel_id: Annotated[str, "ID of the channel to create the webhook in"],
    name: Annotated[str, "Name for the webhook"],
    avatar_url: Annotated[Optional[str], "URL to an image for the webhook's avatar"] = None,
) -> Annotated[Dict, "Details of the created webhook"]:
    """
    Create a webhook in a Discord channel.

    This tool creates a new webhook in the specified channel. Webhooks can
    be used to send messages to the channel from external applications
    without requiring a bot token or user account.

    Example:
        ```python
        create_webhook(
            channel_id="123456789012345678",
            name="My Webhook",
            avatar_url="https://example.com/avatar.png"
        )
        ```
    """
    # Validation
    if not channel_id:
        raise DiscordValidationError(
            message="Channel ID is required",
            developer_message="channel_id parameter was empty or None",
        )

    if not name:
        raise DiscordValidationError(
            message="Webhook name is required",
            developer_message="name parameter was empty or None",
        )

    # Prepare the request payload
    payload = {
        "name": name,
    }

    if avatar_url:
        payload["avatar"] = avatar_url

    # Send the request to Discord API
    response = make_discord_request(
        context=context,
        method="POST",
        endpoint=f"/channels/{channel_id}/webhooks",
        json_data=payload,
        context_message="create webhook",
    )

    # Return in a user-friendly format
    return {
        "id": response.get("id"),
        "name": response.get("name"),
        "channel_id": response.get("channel_id"),
        "token": response.get("token"),
        "url": f"https://discord.com/api/webhooks/{response.get('id')}/{response.get('token')}",
        "application_id": response.get("application_id"),
        "avatar": response.get("avatar"),
    }
