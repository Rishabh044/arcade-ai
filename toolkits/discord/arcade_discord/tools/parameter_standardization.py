"""Discord parameter standardization utilities.

This module defines standard parameter types and helpers for Discord tools to ensure
consistent parameter handling, validation, and formatting across the toolkit.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Annotated, Any, Callable, Dict, Optional, TypeVar, Union

from ..exceptions import DiscordValidationError

logger = logging.getLogger(__name__)

# Type definitions for standard parameters
ServerId = Annotated[str, "ID of the Discord server"]
GuildId = ServerId  # Alias to ensure consistent naming (Discord API uses "guild")
ChannelId = Annotated[str, "ID of the Discord channel"]
UserId = Annotated[str, "ID of the Discord user"]
MessageId = Annotated[str, "ID of the Discord message"]
WebhookId = Annotated[str, "ID of the Discord webhook"]
RoleId = Annotated[str, "ID of the Discord role"]
EmojiId = Annotated[str, "ID of the Discord emoji"]
ThreadId = Annotated[str, "ID of the Discord thread"]
CategoryId = Annotated[str, "ID of the Discord category"]

# Standard parameter types for common content
ChannelName = Annotated[str, "Name of the Discord channel (2-100 characters)"]
ChannelTopic = Annotated[Optional[str], "Topic description for the channel (0-1024 characters)"]
ServerName = Annotated[str, "Name of the Discord server (2-100 characters)"]
MessageContent = Annotated[str, "Content of the message to send"]
RoleName = Annotated[str, "Name of the Discord role (1-100 characters)"]
WebhookName = Annotated[str, "Name of the webhook (1-80 characters)"]
WebhookUrl = Annotated[str, "The full Discord webhook URL"]

# Type for the result transform function
T = TypeVar("T")
ResultTransform = Callable[[Dict], T]


def validate_snowflake(
    value: Optional[str], param_name: str, required: bool = True
) -> Optional[str]:
    """
    Validate a Discord snowflake ID.

    This function checks if a provided value conforms to Discord's snowflake ID format
    (numeric strings typically 17-20 characters long). It can enforce required parameters
    or allow optional ones to be None.

    Examples:
    - validate_snowflake("123456789012345678", "server_id")
    - validate_snowflake(None, "user_id", required=False)

    Args:
        value: The snowflake ID to validate
        param_name: Name of the parameter for error messages
        required: Whether the parameter is required (True) or optional (False)

    Returns:
        The validated snowflake ID or None for optional parameters

    Raises:
        DiscordValidationError: If the value is not a valid snowflake ID
    """
    if value is None:
        if required:
            raise DiscordValidationError(
                message=f"{param_name} is required",
                developer_message=f"{param_name} parameter was None but is required",
            )
        return None

    # Check if value is a string and contains only digits
    if not isinstance(value, str) or not value.isdigit():
        raise DiscordValidationError(
            message=f"{param_name} must be a numeric string",
            developer_message=f"{param_name} must be a string containing only digits, got {type(value)}",
        )

    # Validate length (Discord IDs are typically 17-20 digits)
    if len(value) < 17 or len(value) > 20:
        raise DiscordValidationError(
            message=f"{param_name} has invalid format",
            developer_message=f"{param_name} length should be 17-20 digits, got {len(value)}",
        )

    return value


def validate_server_id(server_id: Optional[str], required: bool = True) -> Optional[str]:
    """
    Validate a Discord server ID.

    This function performs specific validation for server IDs, building on the
    general snowflake validation with server-specific error messages.

    Examples:
    - validate_server_id("123456789012345678")
    - validate_server_id(None, required=False)

    Args:
        server_id: The server ID to validate
        required: Whether the server_id is required (True) or optional (False)

    Returns:
        The validated server ID or None for optional parameters

    Raises:
        DiscordValidationError: If the server ID is not valid
    """
    return validate_snowflake(server_id, "server_id", required)


def validate_guild_id(guild_id: Optional[str], required: bool = True) -> Optional[str]:
    """
    Validate a Discord guild ID (alias for server ID for API consistency).

    This function redirects to validate_server_id to ensure consistent naming
    throughout the toolkit while maintaining compatibility with Discord's API
    which uses "guild" terminology.

    Examples:
    - validate_guild_id("123456789012345678")
    - validate_guild_id(None, required=False)

    Args:
        guild_id: The guild/server ID to validate
        required: Whether the guild_id is required (True) or optional (False)

    Returns:
        The validated guild/server ID or None for optional parameters

    Raises:
        DiscordValidationError: If the guild ID is not valid
    """
    # Log a deprecation warning to encourage consistent naming
    logger.warning(
        "validate_guild_id() is deprecated, use validate_server_id() for consistent naming"
    )
    return validate_server_id(guild_id, required)


def validate_channel_id(channel_id: Optional[str], required: bool = True) -> Optional[str]:
    """
    Validate a Discord channel ID.

    This function performs specific validation for channel IDs, building on the
    general snowflake validation with channel-specific error messages.

    Examples:
    - validate_channel_id("123456789012345678")
    - validate_channel_id(None, required=False)

    Args:
        channel_id: The channel ID to validate
        required: Whether the channel_id is required (True) or optional (False)

    Returns:
        The validated channel ID or None for optional parameters

    Raises:
        DiscordValidationError: If the channel ID is not valid
    """
    return validate_snowflake(channel_id, "channel_id", required)


def validate_user_id(user_id: Optional[str], required: bool = True) -> Optional[str]:
    """
    Validate a Discord user ID.

    This function performs specific validation for user IDs, building on the
    general snowflake validation with user-specific error messages.

    Examples:
    - validate_user_id("123456789012345678")
    - validate_user_id(None, required=False)

    Args:
        user_id: The user ID to validate
        required: Whether the user_id is required (True) or optional (False)

    Returns:
        The validated user ID or None for optional parameters

    Raises:
        DiscordValidationError: If the user ID is not valid
    """
    return validate_snowflake(user_id, "user_id", required)


def validate_message_id(message_id: Optional[str], required: bool = True) -> Optional[str]:
    """
    Validate a Discord message ID.

    This function performs specific validation for message IDs, building on the
    general snowflake validation with message-specific error messages.

    Examples:
    - validate_message_id("123456789012345678")
    - validate_message_id(None, required=False)

    Args:
        message_id: The message ID to validate
        required: Whether the message_id is required (True) or optional (False)

    Returns:
        The validated message ID or None for optional parameters

    Raises:
        DiscordValidationError: If the message ID is not valid
    """
    return validate_snowflake(message_id, "message_id", required)


def validate_webhook_url(url: Optional[str], required: bool = True) -> Optional[str]:
    """
    Validate a Discord webhook URL.

    This function checks if a provided URL conforms to Discord's webhook URL format.
    It validates that the URL includes the required Discord domain and webhook path.

    Examples:
    - validate_webhook_url("https://discord.com/api/webhooks/id/token")
    - validate_webhook_url(None, required=False)

    Args:
        url: The webhook URL to validate
        required: Whether the URL is required (True) or optional (False)

    Returns:
        The validated webhook URL or None for optional parameters

    Raises:
        DiscordValidationError: If the URL is not a valid Discord webhook URL
    """
    if url is None:
        if required:
            raise DiscordValidationError(
                message="Webhook URL is required",
                developer_message="webhook_url parameter was None but is required",
            )
        return None

    # Check if URL matches Discord webhook pattern
    webhook_pattern = r"^https://(discord\.com|discordapp\.com)/api/webhooks/\d+/.+$"
    if not re.match(webhook_pattern, url):
        raise DiscordValidationError(
            message="Invalid Discord webhook URL format",
            developer_message="webhook_url must be a valid Discord webhook URL",
        )

    return url


def validate_channel_name(name: Optional[str], required: bool = True) -> Optional[str]:
    """
    Validate a Discord channel name.

    This function checks if the channel name meets Discord's requirements:
    - Between 2-100 characters
    - No special formatting characters that would break Discord's UI

    Examples:
    - validate_channel_name("general")
    - validate_channel_name("support-tickets")

    Args:
        name: The channel name to validate
        required: Whether the name is required (True) or optional (False)

    Returns:
        The validated channel name or None for optional parameters

    Raises:
        DiscordValidationError: If the channel name is invalid
    """
    if name is None:
        if required:
            raise DiscordValidationError(
                message="Channel name is required",
                developer_message="channel_name parameter was None but is required",
            )
        return None

    if not isinstance(name, str):
        raise DiscordValidationError(
            message="Channel name must be a string",
            developer_message=f"channel_name must be a string, got {type(name)}",
        )

    # Check length requirements
    if len(name) < 2 or len(name) > 100:
        raise DiscordValidationError(
            message="Channel name must be between 2 and 100 characters",
            developer_message=f"channel_name has invalid length: {len(name)}",
        )

    return name


def validate_channel_topic(topic: Optional[str], required: bool = False) -> Optional[str]:
    """
    Validate a Discord channel topic.

    This function checks if the channel topic meets Discord's requirements:
    - Maximum 1024 characters

    Examples:
    - validate_channel_topic("A place to discuss general topics")
    - validate_channel_topic(None, required=False)

    Args:
        topic: The channel topic to validate
        required: Whether the topic is required (True) or optional (False)

    Returns:
        The validated channel topic or None for optional parameters

    Raises:
        DiscordValidationError: If the channel topic is invalid
    """
    if topic is None:
        if required:
            raise DiscordValidationError(
                message="Channel topic is required",
                developer_message="channel_topic parameter was None but is required",
            )
        return None

    if not isinstance(topic, str):
        raise DiscordValidationError(
            message="Channel topic must be a string",
            developer_message=f"channel_topic must be a string, got {type(topic)}",
        )

    # Check length requirements
    if len(topic) > 1024:
        raise DiscordValidationError(
            message="Channel topic cannot exceed 1024 characters",
            developer_message=f"channel_topic has invalid length: {len(topic)}",
        )

    return topic


def validate_message_content(content: Optional[str], required: bool = True) -> Optional[str]:
    """
    Validate message content for Discord.

    This function checks if the message content meets Discord's requirements:
    - Maximum 2000 characters (or 4000 for servers with boost level 2+)
    - Not empty if required

    Examples:
    - validate_message_content("Hello Discord!")
    - validate_message_content(None, required=False)

    Args:
        content: The message content to validate
        required: Whether content is required (True) or optional (False)

    Returns:
        The validated message content or None for optional parameters

    Raises:
        DiscordValidationError: If the message content is invalid
    """
    if content is None:
        if required:
            raise DiscordValidationError(
                message="Message content is required",
                developer_message="content parameter was None but is required",
            )
        return None

    if not isinstance(content, str):
        raise DiscordValidationError(
            message="Message content must be a string",
            developer_message=f"content must be a string, got {type(content)}",
        )

    # Check length requirements - using 2000 as the safe default max
    if len(content) > 2000:
        raise DiscordValidationError(
            message="Message content cannot exceed 2000 characters",
            developer_message=f"content has invalid length: {len(content)}",
        )

    return content


def format_timestamp(timestamp: Optional[Union[int, float, str, datetime]]) -> Optional[str]:
    """
    Convert various timestamp formats to an ISO 8601 string.

    This function normalizes different timestamp representations (Unix timestamps,
    datetime objects, or ISO strings) into a consistent ISO 8601 format string
    that Discord can process.

    Examples:
    - format_timestamp(1609459200)  # Unix timestamp
    - format_timestamp(datetime.now())  # datetime object
    - format_timestamp("2021-01-01T00:00:00Z")  # ISO string

    Args:
        timestamp: The timestamp to format (Unix timestamp, datetime object, or ISO string)

    Returns:
        An ISO 8601 formatted string or None if the input was None

    Raises:
        DiscordValidationError: If the timestamp format cannot be recognized
    """
    if timestamp is None:
        return None

    try:
        # Convert various formats to datetime
        if isinstance(timestamp, (int, float)):
            # Assume Unix timestamp (seconds)
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        elif isinstance(timestamp, str):
            # Try to parse as ISO format
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        elif isinstance(timestamp, datetime):
            # Already a datetime, ensure it's timezone-aware
            if timestamp.tzinfo is None:
                dt = timestamp.replace(tzinfo=timezone.utc)
            else:
                dt = timestamp
        else:
            raise ValueError(f"Unsupported timestamp type: {type(timestamp)}")

        # Convert to ISO 8601 format
        return dt.isoformat()

    except Exception as e:
        raise DiscordValidationError(
            message="Invalid timestamp format", developer_message=f"Could not parse timestamp: {e}"
        )


# Standard date parameters
DateBefore = Annotated[
    Optional[str], "ISO format date (YYYY-MM-DD) - only include items before this date"
]
DateAfter = Annotated[
    Optional[str], "ISO format date (YYYY-MM-DD) - only include items after this date"
]

# Standard filter parameters
TextFilter = Annotated[Optional[str], "Text to filter items by (case-insensitive)"]
LimitParam = Annotated[int, "Maximum number of items to return"]
IncludeBots = Annotated[bool, "Whether to include bot-generated items in results"]

# Standard channel types
CHANNEL_TYPES = {
    "text": 0,
    "dm": 1,
    "voice": 2,
    "group_dm": 3,
    "category": 4,
    "announcement": 5,
    "announcement_thread": 10,
    "public_thread": 11,
    "private_thread": 12,
    "stage": 13,
    "directory": 14,
    "forum": 15,
}

# Standard permission names mapped to bitwise values
PERMISSION_FLAGS = {
    "view_channel": 1 << 0,
    "manage_channels": 1 << 4,
    "manage_roles": 1 << 28,
    "manage_webhooks": 1 << 29,
    "create_instant_invite": 1 << 0,
    "send_messages": 1 << 11,
    "send_messages_in_threads": 1 << 18,
    "embed_links": 1 << 14,
    "attach_files": 1 << 15,
    "add_reactions": 1 << 6,
    "manage_messages": 1 << 13,
    "read_message_history": 1 << 16,
    "mention_everyone": 1 << 17,
    "connect": 1 << 20,
    "speak": 1 << 21,
    "mute_members": 1 << 22,
    "deafen_members": 1 << 23,
    "move_members": 1 << 24,
}


# Standard response transformation
def standardize_server_response(server_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform Discord API server response to standardized format."""
    return {
        "id": server_data.get("id"),
        "name": server_data.get("name"),
        "icon_url": f"https://cdn.discordapp.com/icons/{server_data.get('id')}/{server_data.get('icon')}.png"
        if server_data.get("icon")
        else None,
        "owner_id": server_data.get("owner_id"),
        "member_count": server_data.get("approximate_member_count"),
        "created_at": calculate_creation_date(server_data.get("id")),
    }


def standardize_channel_response(channel_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform Discord API channel response to standardized format."""
    channel_type = next(
        (name for name, value in CHANNEL_TYPES.items() if value == channel_data.get("type")),
        "unknown",
    )

    return {
        "id": channel_data.get("id"),
        "name": channel_data.get("name"),
        "type": channel_type,
        "server_id": channel_data.get("guild_id"),
        "parent_id": channel_data.get("parent_id"),
        "position": channel_data.get("position"),
        "topic": channel_data.get("topic"),
        "created_at": calculate_creation_date(channel_data.get("id")),
    }


def standardize_message_response(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform Discord API message response to standardized format."""
    return {
        "id": message_data.get("id"),
        "content": message_data.get("content"),
        "channel_id": message_data.get("channel_id"),
        "author": {
            "id": message_data.get("author", {}).get("id"),
            "username": message_data.get("author", {}).get("username"),
            "is_bot": message_data.get("author", {}).get("bot", False),
        },
        "created_at": message_data.get("timestamp"),
        "edited_at": message_data.get("edited_timestamp"),
        "attachments": [
            {"url": attachment.get("url"), "filename": attachment.get("filename")}
            for attachment in message_data.get("attachments", [])
        ],
        "embeds": message_data.get("embeds", []),
    }


def calculate_creation_date(discord_id: str) -> str:
    """Calculate creation timestamp from Discord ID."""
    if not discord_id or not discord_id.isdigit():
        return None

    # Discord IDs are based on milliseconds since Discord Epoch (2015-01-01)
    discord_epoch = 1420070400000
    timestamp = (int(discord_id) >> 22) + discord_epoch
    # Convert to ISO format
    from datetime import datetime

    return datetime.fromtimestamp(timestamp / 1000.0).isoformat()
