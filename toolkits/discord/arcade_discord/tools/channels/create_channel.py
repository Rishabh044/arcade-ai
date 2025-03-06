"""Discord channel creation tool.

This module provides a tool for creating new channels in Discord servers.
"""

from typing import Annotated, Dict, Optional

from arcade.core.tool import tool
from arcade.core.tool_context import ToolContext
from arcade.providers.discord import Discord
from arcade_discord.exceptions import DiscordValidationError
from arcade_discord.utils import CHANNEL_WRITE_SCOPES, make_discord_request, parse_channel


@tool(
    requires_auth=Discord(
        scopes=CHANNEL_WRITE_SCOPES,
    )
)
async def create_channel(
    context: ToolContext,
    server_id: Annotated[str, "ID of the server to create the channel in"],
    name: Annotated[str, "Name of the channel to create"],
    type: Annotated[str, "Type of channel to create (text, voice, category, etc.)"],
    topic: Annotated[Optional[str], "Topic/description for the channel"] = None,
    parent_id: Annotated[Optional[str], "ID of the parent category"] = None,
    nsfw: Annotated[bool, "Whether the channel should be NSFW"] = False,
    rate_limit_per_user: Annotated[Optional[int], "Slowmode rate limit in seconds"] = None,
) -> Annotated[Dict, "Details of the created channel"]:
    """
    Create a new channel in a Discord server.

    This tool creates a new channel of the specified type in a Discord server.
    The channel can be customized with various options including topic, category placement,
    NSFW status, and rate limiting.

    Channel types include: text, voice, category, announcement, stage, forum, or media.

    Examples:
    - Create a text channel for a specific topic or discussion
    - Set up a voice channel for voice chat
    - Add a category to organize related channels
    - Create an announcement channel for server-wide notifications

    Returns a dictionary containing:
    - id: The unique ID of the created channel
    - name: The name of the channel
    - type: The type of channel that was created
    - position: The position of the channel in the channel list
    - server_id: The ID of the server containing the channel
    - parent_id: The ID of the parent category (if specified)
    - nsfw: Whether the channel is marked as NSFW
    - topic: The channel topic (if specified)
    """
    # Validation
    if not server_id:
        raise DiscordValidationError(
            message="Server ID is required",
            developer_message="server_id parameter was empty or None",
        )

    if not name:
        raise DiscordValidationError(
            message="Channel name is required",
            developer_message="name parameter was empty or None",
        )

    # Validate and convert channel type to the appropriate integer
    channel_types = {
        "text": 0,
        "dm": 1,
        "voice": 2,
        "group_dm": 3,
        "category": 4,
        "announcement": 5,
        "announcement_thread": 10,
        "public_thread": 11,
        "private_thread": 12,
        "stage": 13,
        "forum": 15,
        "media": 16,
    }

    # Normalize input by converting to lowercase and removing spaces
    normalized_type = type.lower().replace(" ", "_")

    if normalized_type not in channel_types:
        raise DiscordValidationError(
            message=f"Invalid channel type: {type}. Valid types are: {', '.join(channel_types.keys())}",
            developer_message=f"Channel type '{type}' is not supported",
        )

    # Prepare the payload
    payload = {
        "name": name,
        "type": channel_types[normalized_type],
        "nsfw": nsfw,
    }

    if topic:
        payload["topic"] = topic

    if parent_id:
        payload["parent_id"] = parent_id

    if rate_limit_per_user is not None:
        payload["rate_limit_per_user"] = rate_limit_per_user

    # Send the request to Discord API
    response = make_discord_request(
        context=context,
        method="POST",
        endpoint=f"/guilds/{server_id}/channels",
        json_data=payload,
        context_message="create channel",
    )

    # Parse channel data
    channel = parse_channel(response)

    # Return in a user-friendly format
    return {
        "id": channel.id,
        "name": channel.name,
        "type": str(channel.type),
        "position": channel.position,
        "server_id": channel.guild_id,
        "parent_id": channel.parent_id,
        "nsfw": channel.nsfw,
        "topic": channel.topic,
        "created_at": channel.created_at.isoformat() if channel.created_at else None,
    }
