"""Workflow tool for searching messages across Discord channels."""

import asyncio
import re
from typing import Annotated, Dict, Optional

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
async def search_messages(
    context: ToolContext,
    server_id: Annotated[str, "ID of the server to search in"],
    query: Annotated[str, "Text to search for in messages"],
    channel_id: Annotated[
        Optional[str], "Specific channel ID to search in (or None for all channels)"
    ] = None,
    max_results_per_channel: Annotated[int, "Maximum results per channel"] = 25,
    search_in_channel_names: Annotated[
        bool, "Whether to also search in channel names/topics"
    ] = False,
    case_sensitive: Annotated[bool, "Whether the search should be case-sensitive"] = False,
) -> Annotated[Dict, "Messages matching the search query"]:
    """
    Search for messages containing specific text across Discord channels.

    This workflow tool searches for messages containing a specific text query
    across all text channels in a server, or within a specific channel.
    It efficiently combines channel listing and message retrieval.

    Example:
        ```python
        # Search across all channels
        search_messages(
            server_id="123456789012345678",
            query="important announcement"
        )

        # Search in a specific channel
        search_messages(
            server_id="123456789012345678",
            channel_id="987654321098765432",
            query="help me with"
        )
        ```
    """
    # Validation
    if not server_id:
        raise DiscordValidationError(
            message="Server ID is required",
            developer_message="server_id parameter was empty or None",
        )

    if not query:
        raise DiscordValidationError(
            message="Search query is required",
            developer_message="query parameter was empty or None",
        )

    # Prepare search pattern
    pattern_flags = 0 if case_sensitive else re.IGNORECASE
    search_pattern = re.compile(re.escape(query), pattern_flags)

    # Step 1: Get channels to search
    channels_to_search = []

    if channel_id:
        # Get a single channel
        channel_data = make_discord_request(
            context=context,
            method="GET",
            endpoint=f"/channels/{channel_id}",
            context_message="get channel information",
        )

        # Check if channel belongs to the specified server
        if channel_data.get("guild_id") != server_id:
            raise DiscordValidationError(
                message="The specified channel does not belong to the specified server",
                developer_message=f"Channel {channel_id} not in server {server_id}",
            )

        channel = parse_channel(channel_data)
        channels_to_search.append(channel)
    else:
        # Get all channels in the server
        channels_data = make_discord_request(
            context=context,
            method="GET",
            endpoint=f"/guilds/{server_id}/channels",
            context_message="list channels",
        )

        # Only include text channels
        for channel_data in channels_data:
            channel = parse_channel(channel_data)
            if str(channel.type).lower() == "text":
                channels_to_search.append(channel)

    # Step 2: If searching in channel names/topics, filter channels by name/topic
    matching_channels = []
    if search_in_channel_names:
        for channel in channels_to_search:
            channel_name_match = search_pattern.search(channel.name)
            channel_topic_match = channel.topic and search_pattern.search(channel.topic)

            if channel_name_match or channel_topic_match:
                matching_channels.append({
                    "id": channel.id,
                    "name": channel.name,
                    "topic": channel.topic,
                    "match_in": "name" if channel_name_match else "topic",
                })

    # Step 3: Retrieve and search messages from each channel
    async def search_channel_messages(channel):
        try:
            messages_data = make_discord_request(
                context=context,
                method="GET",
                endpoint=f"/channels/{channel.id}/messages",
                params={"limit": 100},  # Max limit to increase search coverage
                context_message=f"get messages from channel {channel.id}",
            )

            # Search through messages
            matches = []
            for message_data in messages_data:
                message = parse_message(message_data)
                if search_pattern.search(message.content):
                    matches.append({
                        "id": message.id,
                        "content": message.content,
                        "author": {
                            "id": message.author.get("id"),
                            "username": message.author.get("username"),
                            "display_name": message.author.get(
                                "display_name", message.author.get("username")
                            ),
                        },
                        "timestamp": message.created_at.isoformat() if message.created_at else None,
                        "match_positions": [
                            m.span() for m in search_pattern.finditer(message.content)
                        ],
                    })

                    # Limit results per channel
                    if len(matches) >= max_results_per_channel:
                        break

            return {
                "channel_id": channel.id,
                "channel_name": channel.name,
                "matches": matches,
            }
        except Exception as e:
            # If we can't search a channel, return empty results
            return {
                "channel_id": channel.id,
                "channel_name": channel.name,
                "matches": [],
                "error": str(e),
            }

    # Create tasks for concurrent execution
    tasks = [search_channel_messages(channel) for channel in channels_to_search]
    search_results = await asyncio.gather(*tasks)

    # Process and format the results
    result = {
        "query": query,
        "case_sensitive": case_sensitive,
        "server_id": server_id,
        "channels_searched": len(channels_to_search),
        "total_matches": 0,
        "message_matches": [],
        "channel_matches": matching_channels if search_in_channel_names else [],
    }

    for channel_result in search_results:
        if channel_result["matches"]:
            result["message_matches"].append({
                "channel_id": channel_result["channel_id"],
                "channel_name": channel_result["channel_name"],
                "matches": channel_result["matches"],
                "match_count": len(channel_result["matches"]),
            })

            result["total_matches"] += len(channel_result["matches"])

    # Sort channels by match count
    result["message_matches"].sort(key=lambda x: x["match_count"], reverse=True)

    return result
