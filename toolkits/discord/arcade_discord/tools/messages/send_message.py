"""Send a message to a Discord channel."""

from typing import Annotated, Dict, Optional

from arcade.context import ToolContext
from arcade.tool import Discord, tool

from arcade_discord.custom_types import Embed
from arcade_discord.tools.parameter_template import message_response_template
from arcade_discord.utils import MESSAGE_WRITE_SCOPES, make_discord_request
from arcade_discord.validation import validate_discord_id, validate_message_content


@tool(requires_auth=Discord(scopes=MESSAGE_WRITE_SCOPES))
async def send_message(
    context: ToolContext,
    channel_id: Annotated[str, "ID of the channel to send the message to"],
    content: Annotated[Optional[str], "Text content of the message"] = None,
    embed: Annotated[Optional[Embed], "Rich embed to include with the message"] = None,
    tts: Annotated[bool, "Whether to send as a TTS message"] = False,
) -> Annotated[Dict, "Details of the sent message"]:
    """Send a new message to a Discord channel.

    Send text content or a rich embed to any accessible Discord channel.

    Args:
        context: Tool execution context with authentication
        channel_id: ID of the Discord channel to send the message to
        content: Text content for the message (optional if embed is provided)
        embed: Rich embed object with formatted content (optional if content is provided)
        tts: Whether to send as a text-to-speech message

    Examples:
        ```python
        # Simple text message
        send_message(channel_id="123456789012345678", content="Hello everyone!")

        # Message with an embed
        embed = Embed(title="Announcement", description="Important update")
        send_message(channel_id="123456789012345678", embed=embed)
        ```

    Returns:
        Dict containing:
        - message_id: The ID of the sent message
        - content: The text content of the message
        - author: Information about the message author
        - channel_id: The channel the message was sent to
        - timestamp: When the message was sent
    """
    # Validate parameters
    validate_discord_id(channel_id, "channel_id")
    validate_message_content(content, embed)

    # Prepare request payload
    payload = {"tts": tts}
    if content:
        payload["content"] = content
    if embed:
        payload["embeds"] = [embed.to_dict()]

    # Send request to Discord API
    response = make_discord_request(
        context=context,
        method="POST",
        endpoint=f"/channels/{channel_id}/messages",
        json_data=payload,
        context_message="send message",
    )

    # Format and return the response
    return message_response_template(response)
