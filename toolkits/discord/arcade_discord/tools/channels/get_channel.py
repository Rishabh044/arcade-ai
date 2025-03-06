"""Tool for retrieving information about a Discord channel."""

from typing import Annotated, Dict

from arcade.context import ToolContext
from arcade.tool import Discord, tool
from arcade_discord.exceptions import DiscordValidationError
from arcade_discord.utils import CHANNEL_READ_SCOPES, make_discord_request, parse_channel


@tool(
    requires_auth=Discord(
        scopes=CHANNEL_READ_SCOPES,
    )
)
async def get_channel(
    context: ToolContext,
    channel_id: Annotated[str, "ID of the channel to retrieve"],
) -> Annotated[Dict, "Details of the Discord channel"]:
    """
    Get detailed information about a Discord channel.

    This tool retrieves comprehensive information about a specific channel in Discord,
    including its name, type, position, permissions, and other channel-specific details.
    It works for all channel types including text channels, voice channels, categories,
    and threads.

    Examples:
    - Get channel details to determine its settings and permissions
    - Verify a channel exists before attempting to send messages to it
    - Retrieve channel information to display in an admin dashboard
    - Check channel settings like slow mode or NSFW status

    Returns a dictionary containing:
    - id: The unique identifier of the channel
    - name: The name of the channel
    - type: The channel type (text, voice, category, etc.)
    - position: The position of the channel in the channel list
    - nsfw: Whether the channel is marked as NSFW
    - parent_id: The ID of the parent category (if applicable)
    - server_id: The ID of the server containing the channel
    - permission_overwrites: List of permission overrides for the channel
    """
    # Validation
    if not channel_id:
        raise DiscordValidationError(
            message="Channel ID is required",
            developer_message="channel_id parameter was empty or None",
        )

    # Send the request to Discord API
    response = make_discord_request(
        context=context,
        method="GET",
        endpoint=f"/channels/{channel_id}",
        context_message="get channel information",
    )

    # Parse channel data
    channel = parse_channel(response)

    # Return in a user-friendly format
    return {
        "id": channel.id,
        "name": channel.name,
        "type": str(channel.type),
        "position": channel.position,
        "nsfw": channel.nsfw,
        "parent_id": channel.parent_id,
        "server_id": channel.guild_id,
        "permission_overwrites": channel.permission_overwrites,
        "rate_limit_per_user": channel.rate_limit_per_user,
        "topic": channel.topic,
        "created_at": channel.created_at.isoformat() if channel.created_at else None,
    }
