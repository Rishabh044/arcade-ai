"""Workflow tool for retrieving recent activity across multiple Discord channels."""

import asyncio
from typing import Annotated, Dict, List

from arcade.context import ToolContext
from arcade.tool import Discord, tool
from arcade_discord.exceptions import DiscordValidationError
from arcade_discord.utils import (
    CHANNEL_SCOPES,
    MESSAGE_SCOPES,
    SERVER_SCOPES,
    make_discord_request,
    parse_channel,
    parse_message,
)


@tool(
    requires_auth=Discord(
        scopes=CHANNEL_SCOPES + MESSAGE_SCOPES + SERVER_SCOPES,
    )
)
async def get_recent_activity(
    context: ToolContext,
    server_id: Annotated[str, "ID of the server to check for activity"],
    channel_types: Annotated[List[str], "Types of channels to include (text, voice, etc.)"] = [
        "text"
    ],
    max_messages_per_channel: Annotated[
        int, "Maximum number of messages to retrieve per channel"
    ] = 10,
    include_channel_info: Annotated[bool, "Include detailed channel information"] = True,
) -> Annotated[Dict, "Recent activity across the server's channels"]:
    """
    Get recent messages and activity across multiple channels in a Discord server.

    This workflow tool combines channel listing and message retrieval to efficiently
    get a snapshot of recent activity across a Discord server. It handles filtering
    by channel type and limits the number of messages per channel.

    Example:
        ```python
        get_recent_activity(
            server_id="123456789012345678",
            channel_types=["text"],
            max_messages_per_channel=5
        )
        ```
    """
    # Validation
    if not server_id:
        raise DiscordValidationError(
            message="Server ID is required",
            developer_message="server_id parameter was empty or None",
        )

    if max_messages_per_channel < 1 or max_messages_per_channel > 100:
        raise DiscordValidationError(
            message="Message limit must be between 1 and 100",
            developer_message=f"Invalid max_messages_per_channel: {max_messages_per_channel}",
        )

    # Step 1: Get server information
    server_info = make_discord_request(
        context=context,
        method="GET",
        endpoint=f"/guilds/{server_id}",
        context_message="get server information",
    )

    # Step 2: Get all channels in the server
    channels_data = make_discord_request(
        context=context,
        method="GET",
        endpoint=f"/guilds/{server_id}/channels",
        context_message="list channels",
    )

    # Parse and filter channels
    channels = []
    for channel_data in channels_data:
        channel = parse_channel(channel_data)

        # Only include channels of the specified types
        if str(channel.type).lower() in [t.lower() for t in channel_types]:
            channels.append(channel)

    # Step 3: Get recent messages from each channel (concurrently)
    async def get_channel_messages(channel):
        try:
            messages_data = make_discord_request(
                context=context,
                method="GET",
                endpoint=f"/channels/{channel.id}/messages",
                params={"limit": max_messages_per_channel},
                context_message=f"get messages from channel {channel.id}",
            )

            return {
                "channel_id": channel.id,
                "channel_name": channel.name,
                "messages": [parse_message(msg) for msg in messages_data],
            }
        except Exception as e:
            # If we can't get messages from a channel, just return empty list
            return {
                "channel_id": channel.id,
                "channel_name": channel.name,
                "messages": [],
                "error": str(e),
            }

    # Create tasks for concurrent execution
    tasks = [get_channel_messages(channel) for channel in channels]
    channel_messages = await asyncio.gather(*tasks)

    # Process and format the results
    result = {
        "server": {
            "id": server_info["id"],
            "name": server_info["name"],
        },
        "channels": [],
        "total_messages_retrieved": 0,
    }

    for channel_data in channel_messages:
        channel_result = {
            "id": channel_data["channel_id"],
            "name": channel_data["channel_name"],
            "message_count": len(channel_data["messages"]),
        }

        # Add channel info if requested
        if include_channel_info:
            for channel in channels:
                if channel.id == channel_data["channel_id"]:
                    channel_result["type"] = str(channel.type)
                    channel_result["topic"] = channel.topic
                    channel_result["nsfw"] = channel.nsfw
                    channel_result["parent_id"] = channel.parent_id
                    break

        # Format messages
        formatted_messages = []
        for msg in channel_data["messages"]:
            formatted_messages.append({
                "id": msg.id,
                "content": msg.content,
                "author": {
                    "id": msg.author.get("id"),
                    "username": msg.author.get("username"),
                    "display_name": msg.author.get("display_name", msg.author.get("username")),
                },
                "timestamp": msg.created_at.isoformat() if msg.created_at else None,
                "has_attachments": len(msg.attachments) > 0,
                "has_embeds": len(msg.embeds) > 0,
            })

        channel_result["messages"] = formatted_messages
        result["channels"].append(channel_result)
        result["total_messages_retrieved"] += len(formatted_messages)

    # Add summary information
    result["active_channels"] = sum(1 for c in result["channels"] if c["message_count"] > 0)
    result["total_channels_checked"] = len(result["channels"])

    return result
