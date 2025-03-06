"""Workflow tool for creating a channel and sending a message in one operation."""

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
async def create_and_send(
    context: ToolContext,
    server_id: Annotated[str, "ID of the server to create the channel in"],
    channel_name: Annotated[str, "Name for the new channel"],
    message_content: Annotated[str, "Content of the message to send"],
    channel_topic: Annotated[Optional[str], "Topic for the new channel"] = None,
    channel_type: Annotated[str, "Type of channel to create"] = "text",
    parent_id: Annotated[Optional[str], "ID of the parent category"] = None,
    embed_title: Annotated[Optional[str], "Title for an embed to include with the message"] = None,
    embed_description: Annotated[Optional[str], "Description for an embed"] = None,
    embed_color: Annotated[Optional[int], "Color for the embed (hex integer)"] = None,
) -> Annotated[Dict, "Results of the channel creation and message sending"]:
    """
    Create a new channel and send a message to it in one operation.

    This workflow tool streamlines the process of setting up a new channel with an
    initial message, which is common when creating announcement channels, support
    threads, or topic-specific discussion channels. The tool handles both channel
    creation and message sending in a single operation.

    Channel creation supports text, announcement, forum, and voice channels with
    optional categorization and topic description. Messages can include rich embeds
    with customizable titles, descriptions, and colors.

    Examples:
    - Create a welcome channel with an introduction message for new members
    - Set up an announcements channel with the first official announcement
    - Create a support channel with initial instructions on how to ask for help
    - Make a new project channel with a kickoff message and embedded timeline

    Returns a dictionary containing:
    - channel: Details about the newly created channel (id, name, type)
    - message: Details about the sent message (id, content)
    - success: Boolean indicating if both operations completed successfully
    """
    # Validation
    if not server_id:
        raise DiscordValidationError(
            message="Server ID is required",
            developer_message="server_id parameter was empty or None",
        )

    if not channel_name:
        raise DiscordValidationError(
            message="Channel name is required",
            developer_message="channel_name parameter was empty or None",
        )

    if not message_content and not (embed_title or embed_description):
        raise DiscordValidationError(
            message="Message content or embed is required",
            developer_message="Neither message_content nor embed parameters provided",
        )

    # Step 1: Create the channel
    # Map channel_type string to Discord API channel type value
    type_mapping = {
        "text": 0,
        "voice": 2,
        "category": 4,
        "announcement": 5,
        "forum": 15,
        "stage": 13,
    }

    if channel_type.lower() not in type_mapping:
        raise DiscordValidationError(
            message=f"Unsupported channel type: {channel_type}",
            developer_message=f"Invalid channel_type: {channel_type}",
        )

    # Prepare the channel creation payload
    channel_payload = {
        "name": channel_name,
        "type": type_mapping[channel_type.lower()],
    }

    if channel_topic:
        channel_payload["topic"] = channel_topic

    if parent_id:
        channel_payload["parent_id"] = parent_id

    # Create the channel
    channel_response = make_discord_request(
        context=context,
        method="POST",
        endpoint=f"/guilds/{server_id}/channels",
        json_data=channel_payload,
        context_message="create channel",
    )

    channel = parse_channel(channel_response)

    # Step 2: Send the message
    # Prepare message payload
    message_payload = {
        "content": message_content,
    }

    # Add embed if provided
    if embed_title or embed_description:
        embed = {
            "title": embed_title,
            "description": embed_description,
            "color": embed_color,
        }
        message_payload["embeds"] = [embed]

    # Send the message
    message_response = make_discord_request(
        context=context,
        method="POST",
        endpoint=f"/channels/{channel.id}/messages",
        json_data=message_payload,
        context_message="send message",
    )

    message = parse_message(message_response)

    # Return combined results
    return {
        "channel": {
            "id": channel.id,
            "name": channel.name,
            "type": str(channel.type),
            "topic": channel.topic,
            "server_id": channel.guild_id,
            "parent_id": channel.parent_id,
        },
        "message": {
            "id": message.id,
            "content": message.content,
            "author": {
                "id": message.author.get("id"),
                "username": message.author.get("username"),
                "display_name": message.author.get("display_name"),
            },
            "timestamp": message.created_at.isoformat() if message.created_at else None,
            "embeds": message.embeds,
        },
        "success": True,
    }
