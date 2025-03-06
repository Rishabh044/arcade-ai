"""Tool for listing channels in a Discord server."""

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
async def list_channels(
    context: ToolContext,
    server_id: Annotated[str, "ID of the server (guild) to list channels from"],
) -> Annotated[Dict, "List of channels in the server"]:
    """
    List channels in a Discord server.

    This tool retrieves all channels from a specified Discord server (guild).
    The result includes text channels, voice channels, and categories,
    with details like ID, name, type, and position.

    Examples:
    - Get a list of all channels in a server for navigation
    - Find specific channels by type or name
    - Map the structure of categories and their child channels
    - Identify channels for targeted messaging or moderation

    Returns a dictionary containing:
    - categories: List of category channels with their details
    - text_channels: List of text channels with their details
    - voice_channels: List of voice channels with their details
    - other_channels: List of other channel types with their details
    - total_channels: Total count of all channels in the server
    - server: Basic information about the server
    """
    # Validation
    if not server_id:
        raise DiscordValidationError(
            message="Server ID is required",
            developer_message="server_id parameter was empty or None",
        )

    # Send the request to Discord API
    response = make_discord_request(
        context=context,
        method="GET",
        endpoint=f"/guilds/{server_id}/channels",
        context_message="list channels",
    )

    # Get server information
    server_info = make_discord_request(
        context=context,
        method="GET",
        endpoint=f"/guilds/{server_id}",
        context_message="retrieve server information",
    )

    # Parse channels and organize by type
    text_channels = []
    voice_channels = []
    categories = []
    other_channels = []

    for channel_data in response:
        channel = parse_channel(channel_data)

        channel_info = {
            "id": channel.id,
            "name": channel.name,
            "type": str(channel.type),
            "position": channel.position,
            "parent_id": channel.parent_id,
            "nsfw": channel.nsfw,
        }

        # Categorize channels
        if channel.type.lower() == "text":
            text_channels.append(channel_info)
        elif channel.type.lower() == "voice":
            voice_channels.append(channel_info)
        elif channel.type.lower() == "category":
            categories.append(channel_info)
        else:
            other_channels.append(channel_info)

    # Return in a user-friendly format
    return {
        "server": {
            "id": server_info["id"],
            "name": server_info["name"],
        },
        "categories": categories,
        "text_channels": text_channels,
        "voice_channels": voice_channels,
        "other_channels": other_channels,
        "total_channels": len(response),
    }
