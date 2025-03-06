"""Tool for deleting Discord messages."""

from typing import Annotated, Dict

from arcade.context import ToolContext
from arcade.tool import Discord, tool
from arcade_discord.exceptions import DiscordValidationError
from arcade_discord.utils import MESSAGE_WRITE_SCOPES, make_discord_request


@tool(
    requires_auth=Discord(
        scopes=MESSAGE_WRITE_SCOPES,
    )
)
async def delete_message(
    context: ToolContext,
    channel_id: Annotated[str, "ID of the channel containing the message"],
    message_id: Annotated[str, "ID of the message to delete"],
) -> Annotated[Dict, "Result of the delete operation"]:
    """
    Delete a Discord message.

    This tool deletes a message from a Discord channel. The bot must have
    proper permissions to delete the message. You can only delete messages sent by the bot
    itself or messages in channels where the bot has the MANAGE_MESSAGES permission.

    Examples:
    - Delete a bot's own message in a channel
    - Remove inappropriate messages in a moderated channel
    - Clean up old announcements or temporary information
    - Remove test messages during development

    Returns a dictionary containing:
    - success: Boolean indicating successful deletion
    - message: Confirmation message
    - channel_id: ID of the channel where the message was deleted
    - message_id: ID of the deleted message
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

    # Send the request to Discord API
    make_discord_request(
        context=context,
        method="DELETE",
        endpoint=f"/channels/{channel_id}/messages/{message_id}",
        context_message="delete message",
    )

    # Return success result
    return {
        "success": True,
        "message": "Message successfully deleted",
        "channel_id": channel_id,
        "message_id": message_id,
    }
