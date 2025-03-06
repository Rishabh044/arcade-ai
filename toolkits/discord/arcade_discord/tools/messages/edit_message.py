"""Tool for editing Discord messages."""

from typing import Annotated, Dict, Optional

from arcade.context import ToolContext
from arcade.tool import Discord, tool
from arcade_discord.custom_types import Embed
from arcade_discord.exceptions import DiscordValidationError
from arcade_discord.utils import MESSAGE_WRITE_SCOPES, make_discord_request, parse_message


@tool(
    requires_auth=Discord(
        scopes=MESSAGE_WRITE_SCOPES,
    )
)
async def edit_message(
    context: ToolContext,
    channel_id: Annotated[str, "ID of the channel containing the message"],
    message_id: Annotated[str, "ID of the message to edit"],
    content: Annotated[Optional[str], "New text content for the message"] = None,
    embed: Annotated[Optional[Embed], "New rich embed for the message"] = None,
) -> Annotated[Dict, "Details of the edited message"]:
    """
    Edit an existing Discord message.

    This tool modifies a message previously sent by the authenticated bot.
    You can update the text content, replace embeds, or both. Note that you
    can only edit messages that were sent by the bot itself.

    Examples:
    - Correct typos or errors in previously sent messages
    - Update information that has changed since the original message
    - Add or replace rich embeds with updated content
    - Change formatting or appearance of a message

    Returns a dictionary containing:
    - message_id: The ID of the edited message
    - content: The updated text content
    - channel_id: The channel where the message is located
    - author: Details about the message author
    - edited_at: Timestamp when the message was edited
    - embeds: Any rich embeds included in the message
    """
    # Validation
    if not channel_id:
        raise DiscordValidationError(
            message="Channel ID is required",
            developer_message="channel_id parameter was empty or None",
        )

    if not message_id:
        raise DiscordValidationError(
            message="Message ID is required",
            developer_message="message_id parameter was empty or None",
        )

    if content is None and embed is None:
        raise DiscordValidationError(
            message="Either content or embed must be provided",
            developer_message="Both content and embed parameters were None",
        )

    # Prepare the request payload
    payload = {}

    if content is not None:
        payload["content"] = content

    if embed is not None:
        payload["embeds"] = [embed.to_dict()]

    # Send the request to Discord API
    response = make_discord_request(
        context=context,
        method="PATCH",
        endpoint=f"/channels/{channel_id}/messages/{message_id}",
        json_data=payload,
        context_message="edit message",
    )

    # Parse and return the message data
    message = parse_message(response)

    # Return in a user-friendly format
    return {
        "message_id": message.id,
        "content": message.content,
        "channel_id": message.channel_id,
        "author": {
            "id": message.author.get("id"),
            "username": message.author.get("username"),
            "display_name": message.author.get("display_name"),
        },
        "edited_at": message.edited_at.isoformat() if message.edited_at else None,
        "embeds": message.embeds,
    }
