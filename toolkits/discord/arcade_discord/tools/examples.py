"""Convenience tools combining multiple Discord operations."""

from typing import Annotated, Dict, Optional

from arcade.context import ToolContext
from arcade.tool import Discord, tool

from arcade_discord.custom_types import ChannelType, Embed
from arcade_discord.tools.channels import create_channel
from arcade_discord.tools.messages import send_message
from arcade_discord.tools.webhooks import create_webhook, send_webhook_message
from arcade_discord.utils import (
    CHANNEL_WRITE_SCOPES,
    MESSAGE_WRITE_SCOPES,
    WEBHOOK_SCOPES,
)
from arcade_discord.validation import validate_channel_name, validate_discord_id


@tool(requires_auth=Discord(scopes=CHANNEL_WRITE_SCOPES + MESSAGE_WRITE_SCOPES))
async def create_and_post(
    context: ToolContext,
    server_id: Annotated[str, "ID of the server to create the channel in"],
    channel_name: Annotated[str, "Name of the channel to create"],
    message_content: Annotated[str, "Content of the message to post"],
    channel_topic: Annotated[Optional[str], "Description of the channel"] = None,
    is_announcement: Annotated[
        bool, "Whether to create an announcement channel"
    ] = False,
) -> Annotated[Dict, "Details of the created channel and posted message"]:
    """Create a channel and post an initial message in one operation.

    Args:
        context: Tool execution context
        server_id: ID of the Discord server for the new channel
        channel_name: Name for the new channel (will be normalized)
        message_content: Initial message to post in the new channel
        channel_topic: Optional description for the channel
        is_announcement: Whether to create an announcement-type channel

    Examples:
        ```python
        # Create a help channel with welcome message
        create_and_post(
            server_id="123456789012345678",
            channel_name="help-desk",
            message_content="Welcome to the Help Desk!"
        )
        ```

    Returns:
        Dict containing:
        - channel: Details of the created channel
        - message: Details of the posted message
    """
    # Validate and normalize inputs
    validate_discord_id(server_id, "server_id")
    channel_name = validate_channel_name(channel_name)

    # Create channel
    channel_type = ChannelType.ANNOUNCEMENT if is_announcement else ChannelType.TEXT
    channel = await create_channel(
        context=context,
        server_id=server_id,
        name=channel_name,
        type=channel_type,
        topic=channel_topic,
    )

    # Send initial message
    message = await send_message(
        context=context,
        channel_id=channel["id"],
        content=message_content,
    )

    return {"channel": channel, "message": message}


@tool(requires_auth=Discord(scopes=WEBHOOK_SCOPES + CHANNEL_WRITE_SCOPES))
async def setup_webhook_integration(
    context: ToolContext,
    channel_id: Annotated[str, "ID of the channel to create the webhook in"],
    webhook_name: Annotated[str, "Name of the webhook"],
    test_message: Annotated[Optional[str], "Test message to send"] = None,
    avatar_url: Annotated[Optional[str], "URL for webhook avatar"] = None,
) -> Annotated[Dict, "Details of the created webhook and test message"]:
    """Create a webhook and optionally test it with a message.

    Args:
        context: Tool execution context
        channel_id: ID of the Discord channel for the webhook
        webhook_name: Name for the webhook (appears as sender name)
        test_message: Optional message to test the webhook
        avatar_url: Optional avatar URL for the webhook

    Examples:
        ```python
        # Create webhook with test message
        setup_webhook_integration(
            channel_id="123456789012345678",
            webhook_name="Alerts",
            test_message="Testing the webhook"
        )
        ```

    Returns:
        Dict containing:
        - webhook: Details of the created webhook
        - test_message: Details of the test message (if sent)
    """
    # Validate inputs
    validate_discord_id(channel_id, "channel_id")

    # Create webhook
    webhook = await create_webhook(
        context=context,
        channel_id=channel_id,
        name=webhook_name,
        avatar_url=avatar_url,
    )

    result = {"webhook": webhook}

    # Send test message if provided
    if test_message:
        message = await send_webhook_message(
            context=context,
            webhook_url=webhook["url"],
            content=test_message,
        )
        result["test_message"] = message

    return result


@tool(requires_auth=Discord(scopes=MESSAGE_WRITE_SCOPES))
async def send_formatted_message(
    context: ToolContext,
    channel_id: Annotated[str, "ID of the channel to send the message to"],
    title: Annotated[str, "Title for the message embed"],
    description: Annotated[str, "Main content for the message embed"],
    color: Annotated[Optional[int], "Color code for the embed (decimal RGB)"] = None,
    fields: Annotated[Optional[Dict[str, str]], "Field names and values"] = None,
) -> Annotated[Dict, "Details of the sent message"]:
    """Send a professionally formatted message with embed.

    Args:
        context: Tool execution context
        channel_id: ID of the Discord channel to message
        title: Title displayed at the top of the embed
        description: Main content text of the embed
        color: Color for the embed's left border (decimal RGB)
        fields: Dictionary of field names to values

    Examples:
        ```python
        # Status update with fields
        send_formatted_message(
            channel_id="123456789012345678",
            title="Status Update",
            description="Weekly summary",
            color=0x00ff00,  # Green
            fields={
                "New Features": "- Feature A\n- Feature B",
                "Fixes": "- Bug fix 1"
            }
        )
        ```

    Returns:
        Dict containing details of the sent message
    """
    # Validate inputs
    validate_discord_id(channel_id, "channel_id")

    # Create embed
    embed = Embed(
        title=title,
        description=description,
        color=color or 0x3498DB,  # Default to Discord blue
    )

    # Add fields if provided
    if fields:
        for name, value in fields.items():
            embed.fields.append({"name": name, "value": value, "inline": False})

    # Send message
    return await send_message(
        context=context,
        channel_id=channel_id,
        embed=embed,
    )
