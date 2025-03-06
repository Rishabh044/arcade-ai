"""Tool for retrieving messages from Discord channels."""

from typing import Annotated, Dict, Optional

from arcade.context import ToolContext
from arcade.tool import Discord, tool
from arcade_discord.exceptions import DiscordValidationError
from arcade_discord.utils import MESSAGE_READ_SCOPES, make_discord_request, parse_message


@tool(
    requires_auth=Discord(
        scopes=MESSAGE_READ_SCOPES,
    )
)
async def list_messages(
    context: ToolContext,
    channel_id: Annotated[str, "ID of the channel to retrieve messages from"],
    limit: Annotated[int, "Maximum number of messages to retrieve (1-100)"] = 50,
    before: Annotated[Optional[str], "Get messages before this message ID"] = None,
    after: Annotated[Optional[str], "Get messages after this message ID"] = None,
    around: Annotated[Optional[str], "Get messages around this message ID"] = None,
) -> Annotated[Dict, "A dictionary containing messages from the channel"]:
    """
    List messages from a Discord channel.

    This tool retrieves a batch of messages from a specified Discord channel.
    Messages can be filtered using the before, after, or around parameters to
    navigate through message history. Each message includes its content, author,
    timestamp, and other metadata.

    Examples:
    - Retrieve recent messages in a support channel to track user issues
    - Get messages before a specific message ID to view older conversation
    - Fetch messages around a specific message to see its context
    - Monitor channel activity by periodically retrieving the latest messages

    Returns a dictionary containing:
    - messages: List of message objects with their content and metadata
    - channel_id: ID of the channel the messages are from
    - total_count: Number of messages retrieved
    """
    # Validation
    if not channel_id:
        raise DiscordValidationError(
            message="Channel ID is required",
            developer_message="channel_id parameter was empty or None",
        )

    if limit < 1 or limit > 100:
        raise DiscordValidationError(
            message="Limit must be between 1 and 100",
            developer_message=f"Invalid limit value: {limit}",
        )

    # Can only use one of before, after, or around
    params_count = sum(1 for p in [before, after, around] if p is not None)
    if params_count > 1:
        raise DiscordValidationError(
            message="Can only use one of before, after, or around",
            developer_message="Multiple pagination parameters provided",
        )

    # Prepare query parameters
    params = {"limit": limit}
    if before:
        params["before"] = before
    if after:
        params["after"] = after
    if around:
        params["around"] = around

    # Send the request to Discord API
    response = make_discord_request(
        context=context,
        method="GET",
        endpoint=f"/channels/{channel_id}/messages",
        params=params,
        context_message="list messages",
    )

    # Parse messages
    messages = []
    for message_data in response:
        message = parse_message(message_data)
        messages.append({
            "id": message.id,
            "content": message.content,
            "author": {
                "id": message.author.get("id"),
                "username": message.author.get("username"),
                "display_name": message.author.get("display_name"),
            },
            "created_at": message.created_at.isoformat() if message.created_at else None,
            "edited_at": message.edited_at.isoformat() if message.edited_at else None,
            "attachments": message.attachments,
            "embeds": message.embeds,
            "reactions": message.reactions,
            "channel_id": message.channel_id,
        })

    # Return in a user-friendly format
    return {
        "messages": messages,
        "channel_id": channel_id,
        "total_count": len(messages),
    }
