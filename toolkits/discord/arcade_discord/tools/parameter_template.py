"""Parameter templates for Discord tools.

This module provides reusable templates for parameter validation and documentation
to ensure consistency across all Discord toolkit tools.
"""

from typing import Annotated, Dict, Optional

from arcade_discord.custom_types import Embed

# Common parameter templates with standardized descriptions

# IDs - Always required by default
ChannelIdParam = Annotated[str, "ID of the Discord channel"]
MessageIdParam = Annotated[str, "ID of the Discord message"]
ServerIdParam = Annotated[str, "ID of the Discord server"]
GuildIdParam = ServerIdParam  # Alias for consistency with Discord API terminology
UserIdParam = Annotated[str, "ID of the Discord user"]
RoleIdParam = Annotated[str, "ID of the Discord role"]
WebhookIdParam = Annotated[str, "ID of the Discord webhook"]
EmojiIdParam = Annotated[str, "ID of the Discord emoji"]
ThreadIdParam = Annotated[str, "ID of the Discord thread"]

# Content parameters
MessageContentParam = Annotated[str, "Text content of the message"]
OptionalMessageContent = Annotated[Optional[str], "Text content of the message"]
EmbedParam = Annotated[Optional[Embed], "Rich embed to include with the message"]
ChannelNameParam = Annotated[str, "Name of the channel (2-100 characters)"]
ChannelTopicParam = Annotated[
    Optional[str], "Topic/description for the channel (0-1024 characters)"
]
ServerNameParam = Annotated[str, "Name of the Discord server (2-100 characters)"]
RoleNameParam = Annotated[str, "Name of the Discord role (1-100 characters)"]
WebhookNameParam = Annotated[str, "Name of the webhook (1-80 characters)"]
WebhookUrlParam = Annotated[str, "The full Discord webhook URL"]

# Flag parameters
NsfwParam = Annotated[bool, "Whether the channel should be NSFW"]
TtsParam = Annotated[bool, "Whether to send as a TTS (text-to-speech) message"]

# Limit parameters
MessageLimitParam = Annotated[int, "Maximum number of messages to retrieve (1-100)"]
ServerLimitParam = Annotated[int, "Maximum number of servers to retrieve (1-200)"]
MemberLimitParam = Annotated[int, "Maximum number of members to retrieve (1-1000)"]

# Template return type documentation strings
# Use these as the second element in Annotated[Dict, "..."] for return types

# Message-related return docs
MESSAGE_SENT_DOC = "Details of the sent message"
MESSAGE_EDITED_DOC = "Details of the edited message"
MESSAGE_DELETED_DOC = "Result of the delete operation"
MESSAGES_LIST_DOC = "List of messages from the channel"

# Channel-related return docs
CHANNEL_CREATED_DOC = "Details of the created channel"
CHANNEL_UPDATED_DOC = "Details of the updated channel"
CHANNEL_DELETED_DOC = "Result of the delete operation"
CHANNELS_LIST_DOC = "List of channels in the server"

# Server-related return docs
SERVER_INFO_DOC = "Details about the Discord server"
SERVERS_LIST_DOC = "List of Discord servers the bot is a member of"

# User-related return docs
USER_INFO_DOC = "Details about the Discord user"
USERS_LIST_DOC = "List of users with their details"

# Role-related return docs
ROLE_CREATED_DOC = "Details of the created role"
ROLE_ASSIGNED_DOC = "Result of the role assignment operation"
ROLES_LIST_DOC = "List of roles in the server"


# Standard response templates for consistent return formats
def message_response_template(message_data: Dict) -> Dict:
    """Standard template for message response data."""
    return {
        "message_id": message_data.get("id"),
        "content": message_data.get("content"),
        "author": {
            "id": message_data.get("author", {}).get("id"),
            "username": message_data.get("author", {}).get("username"),
            "display_name": message_data.get("author", {}).get("display_name"),
        },
        "channel_id": message_data.get("channel_id"),
        "timestamp": message_data.get("timestamp"),
        "edited_at": message_data.get("edited_timestamp"),
        "embeds": message_data.get("embeds", []),
        "attachments": message_data.get("attachments", []),
    }


def channel_response_template(channel_data: Dict) -> Dict:
    """Standard template for channel response data."""
    return {
        "id": channel_data.get("id"),
        "name": channel_data.get("name"),
        "type": channel_data.get("type"),
        "position": channel_data.get("position"),
        "server_id": channel_data.get("guild_id"),
        "parent_id": channel_data.get("parent_id"),
        "nsfw": channel_data.get("nsfw", False),
        "topic": channel_data.get("topic"),
    }


def server_response_template(server_data: Dict) -> Dict:
    """Standard template for server response data."""
    return {
        "id": server_data.get("id"),
        "name": server_data.get("name"),
        "icon": server_data.get("icon"),
        "owner_id": server_data.get("owner_id"),
        "member_count": server_data.get("approximate_member_count"),
        "features": server_data.get("features", []),
        "description": server_data.get("description"),
    }


def user_response_template(user_data: Dict) -> Dict:
    """Standard template for user response data."""
    return {
        "id": user_data.get("id"),
        "username": user_data.get("username"),
        "display_name": user_data.get("display_name") or user_data.get("username"),
        "discriminator": user_data.get("discriminator"),
        "avatar": user_data.get("avatar"),
        "bot": user_data.get("bot", False),
    }


def role_response_template(role_data: Dict) -> Dict:
    """Standard template for role response data."""
    return {
        "id": role_data.get("id"),
        "name": role_data.get("name"),
        "color": role_data.get("color"),
        "position": role_data.get("position"),
        "permissions": role_data.get("permissions"),
        "mentionable": role_data.get("mentionable", False),
        "hoist": role_data.get("hoist", False),
    }
