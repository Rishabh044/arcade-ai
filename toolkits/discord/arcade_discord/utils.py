"""Utility functions for Discord API interactions."""

from typing import Any, Dict, Optional, Union

import requests

from arcade.context import ToolContext
from arcade.exceptions import ToolError
from arcade_discord.custom_types import Channel, Message, Server
from arcade_discord.exceptions import (
    DiscordAuthError,
    DiscordPermissionError,
    DiscordRateLimitError,
    DiscordRequestError,
    DiscordResourceNotFoundError,
    DiscordToolError,
    DiscordValidationError,
)

# Discord API base URL
API_BASE_URL = "https://discord.com/api/v10"

# ------------------------------------------------------------------------------
# Discord authorization scopes
# ------------------------------------------------------------------------------

# Core scopes
BOT_SCOPE = "bot"
COMMANDS_SCOPE = "applications.commands"
WEBHOOK_SCOPE = "webhook.incoming"

# Resource-specific scopes
MESSAGE_READ_SCOPE = "messages.read"
MESSAGE_WRITE_SCOPE = "messages.write"
CHANNEL_READ_SCOPE = "channels.read"
CHANNEL_WRITE_SCOPE = "channels.write"
GUILD_READ_SCOPE = "guilds.read"
GUILD_MEMBERS_READ_SCOPE = "guilds.members.read"
GUILD_JOIN_SCOPE = "guilds.join"
GUILD_ROLES_WRITE_SCOPE = "guilds.roles.write"

# Common scope combinations
BOT_SCOPES = [BOT_SCOPE, COMMANDS_SCOPE]
MESSAGE_READ_SCOPES = [BOT_SCOPE, MESSAGE_READ_SCOPE]
MESSAGE_WRITE_SCOPES = [BOT_SCOPE, MESSAGE_WRITE_SCOPE]
MESSAGE_SCOPES = [BOT_SCOPE, MESSAGE_READ_SCOPE, MESSAGE_WRITE_SCOPE]
CHANNEL_READ_SCOPES = [BOT_SCOPE, CHANNEL_READ_SCOPE]
CHANNEL_WRITE_SCOPES = [BOT_SCOPE, CHANNEL_WRITE_SCOPE]
CHANNEL_SCOPES = [BOT_SCOPE, CHANNEL_READ_SCOPE, CHANNEL_WRITE_SCOPE]
GUILD_READ_SCOPES = [BOT_SCOPE, GUILD_READ_SCOPE]
GUILD_MEMBERS_READ_SCOPES = [BOT_SCOPE, GUILD_MEMBERS_READ_SCOPE]
GUILD_JOIN_SCOPES = [BOT_SCOPE, GUILD_JOIN_SCOPE]
GUILD_ROLES_WRITE_SCOPES = [BOT_SCOPE, GUILD_ROLES_WRITE_SCOPE]
WEBHOOK_SCOPES = [WEBHOOK_SCOPE]

# Thread-related scopes (same as channels)
THREAD_SCOPES = CHANNEL_SCOPES

# ------------------------------------------------------------------------------
# Request/Response Handling
# ------------------------------------------------------------------------------


def _handle_discord_errors(response: requests.Response, context_message: str) -> None:
    """Handle Discord API errors based on HTTP response.

    Args:
        response: The HTTP response from Discord API
        context_message: Context message describing the operation being performed

    Raises:
        Various Discord exceptions based on the error
    """
    if response.status_code == 200:
        return

    try:
        error_data = response.json()
    except ValueError:
        error_data = {"message": response.text or "Unknown error"}

    error_message = error_data.get("message", "Unknown error")
    developer_message = f"{error_message} (Code: {response.status_code})"

    if response.status_code == 401:
        raise DiscordAuthError(
            message="Authentication failed. Please make sure your Discord token is valid.",
            developer_message=developer_message,
        )

    if response.status_code == 403:
        raise DiscordPermissionError(
            message=f"You don't have permission to {context_message}.",
            developer_message=developer_message,
        )

    if response.status_code == 404:
        raise DiscordResourceNotFoundError(
            message=f"The Discord resource was not found while trying to {context_message}.",
            developer_message=developer_message,
        )

    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After", "unknown")
        raise DiscordRateLimitError(
            message=f"Discord rate limit exceeded. Please try again after {retry_after} seconds.",
            developer_message=f"Rate limit hit: {developer_message}. Retry after: {retry_after}",
        )

    # General error for all other cases
    raise DiscordRequestError(
        message=f"Failed to {context_message}. {error_message}",
        developer_message=developer_message,
    )


def make_discord_request(
    context: ToolContext,
    method: str,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    context_message: str = "perform Discord operation",
) -> Dict[str, Any]:
    """Make a request to the Discord API.

    Args:
        context: The tool context containing authorization
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        endpoint: API endpoint path (without the base URL)
        params: URL query parameters
        data: Form data
        json_data: JSON data
        context_message: Context message for error handling

    Returns:
        The JSON response from Discord API

    Raises:
        DiscordToolError: If the request fails
    """
    if not context.authorization or not context.authorization.token:
        raise DiscordAuthError(
            message="Discord authorization is required for this tool.",
            developer_message="No authorization token provided in context",
        )

    headers = {
        "Authorization": f"Bearer {context.authorization.token}",
        "Content-Type": "application/json",
    }

    url = f"{API_BASE_URL}{endpoint}"

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            data=data,
            json=json_data,
            timeout=30,
        )

        _handle_discord_errors(response, context_message)

        if response.status_code == 204:  # No content
            return {}

        return response.json()

    except requests.RequestException as e:
        raise DiscordRequestError(
            message=f"Failed to {context_message} due to a network error.",
            developer_message=f"Request error: {e!s}",
        )
    except ToolError:
        # Re-raise any of our custom exceptions
        raise
    except Exception as e:
        raise DiscordToolError(
            message=f"An unexpected error occurred while trying to {context_message}.",
            developer_message=f"Unexpected error: {e!s}",
        )


# ------------------------------------------------------------------------------
# Data Parsing Functions
# ------------------------------------------------------------------------------


def parse_message(message_data: Dict[str, Any]) -> Message:
    """Parse Discord API message data into Message object.

    Args:
        message_data: Raw message data from Discord API

    Returns:
        Parsed Message object
    """
    created_at = message_data.get("timestamp")
    if created_at:
        from datetime import datetime

        created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

    edited_at = message_data.get("edited_timestamp")
    if edited_at and edited_at != "null":
        edited_at = datetime.fromisoformat(edited_at.replace("Z", "+00:00"))
    else:
        edited_at = None

    return Message(
        id=message_data["id"],
        content=message_data["content"],
        author=message_data["author"],
        channel_id=message_data["channel_id"],
        created_at=created_at,
        embeds=message_data.get("embeds", []),
        attachments=message_data.get("attachments", []),
        mentions=message_data.get("mentions", []),
        mention_roles=message_data.get("mention_roles", []),
        edited_at=edited_at,
    )


def parse_channel(channel_data: Dict[str, Any]) -> Channel:
    """Parse Discord API channel data into Channel object.

    Args:
        channel_data: Raw channel data from Discord API

    Returns:
        Parsed Channel object
    """
    from arcade_discord.custom_types import ChannelType

    # Map Discord channel types to our enum
    type_mapping = {
        0: ChannelType.TEXT,
        1: ChannelType.VOICE,
        2: ChannelType.CATEGORY,
        3: ChannelType.ANNOUNCEMENT,
        4: ChannelType.STORE,
        5: ChannelType.FORUM,
        10: ChannelType.ANNOUNCEMENT,
        13: ChannelType.STAGE,
    }

    channel_type = type_mapping.get(channel_data.get("type", 0), ChannelType.TEXT)

    return Channel(
        id=channel_data["id"],
        type=channel_type,
        name=channel_data["name"],
        guild_id=channel_data.get("guild_id"),
        position=channel_data.get("position"),
        topic=channel_data.get("topic"),
        nsfw=channel_data.get("nsfw", False),
        parent_id=channel_data.get("parent_id"),
    )


def parse_server(server_data: Dict[str, Any]) -> Server:
    """Parse Discord API server (guild) data into Server object.

    Args:
        server_data: Raw server data from Discord API

    Returns:
        Parsed Server object
    """
    return Server(
        id=server_data["id"],
        name=server_data["name"],
        owner_id=server_data.get("owner_id"),
        icon=server_data.get("icon"),
        features=server_data.get("features", []),
        member_count=server_data.get("approximate_member_count"),
    )


def format_channel_for_response(channel_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a channel response in a standardized, user-friendly way.

    Args:
        channel_data: Raw channel data from Discord API

    Returns:
        A standardized channel response dictionary
    """
    # Map numeric channel types to readable strings
    channel_type_names = {
        0: "text",
        1: "voice",
        2: "category",
        3: "announcement",
        4: "store",
        5: "forum",
        10: "announcement_thread",
        11: "public_thread",
        12: "private_thread",
        13: "stage",
        14: "directory",
        15: "forum_thread",
    }

    # Extract the type as an integer
    channel_type = channel_data.get("type", 0)

    # Format the response
    return {
        "id": channel_data.get("id"),
        "name": channel_data.get("name"),
        "type": channel_type_names.get(channel_type, "unknown"),
        "server_id": channel_data.get("guild_id"),  # Note the naming standardization
        "topic": channel_data.get("topic"),
        "position": channel_data.get("position"),
        "nsfw": channel_data.get("nsfw", False),
        "category_id": channel_data.get("parent_id"),
        "rate_limit_per_user": channel_data.get("rate_limit_per_user"),
        "permissions": {
            "view": True,  # Default value, actual permissions would require additional logic
        },
    }


def format_server_for_response(server_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a server response in a standardized, user-friendly way.

    Args:
        server_data: Raw server data from Discord API

    Returns:
        A standardized server response dictionary
    """
    return {
        "id": server_data.get("id"),
        "name": server_data.get("name"),
        "owner_id": server_data.get("owner_id"),
        "icon_url": _get_server_icon_url(server_data.get("id"), server_data.get("icon")),
        "member_count": server_data.get("approximate_member_count"),
        "features": server_data.get("features", []),
        "created_at": calculate_creation_date(server_data.get("id")),
    }


def format_message_for_response(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a message response in a standardized, user-friendly way.

    Args:
        message_data: Raw message data from Discord API

    Returns:
        A standardized message response dictionary
    """
    return {
        "id": message_data.get("id"),
        "content": message_data.get("content", ""),
        "author": {
            "id": message_data.get("author", {}).get("id"),
            "username": message_data.get("author", {}).get("username"),
            "display_name": message_data.get("author", {}).get("display_name"),
        },
        "channel_id": message_data.get("channel_id"),
        "timestamp": message_data.get("timestamp"),
        "edited_timestamp": message_data.get("edited_timestamp"),
        "embeds": message_data.get("embeds", []),
        "attachments": [
            {
                "id": attachment.get("id"),
                "filename": attachment.get("filename"),
                "size": attachment.get("size"),
                "url": attachment.get("url"),
                "content_type": attachment.get("content_type"),
            }
            for attachment in message_data.get("attachments", [])
        ],
        "mentions": [user.get("id") for user in message_data.get("mentions", [])],
    }


def format_webhook_for_response(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a webhook response in a standardized, user-friendly way.

    Args:
        webhook_data: Raw webhook data from Discord API

    Returns:
        A standardized webhook response dictionary
    """
    # Mask webhook token for security
    token = webhook_data.get("token")
    masked_token = f"{token[:3]}...{token[-3:]}" if token else None

    return {
        "id": webhook_data.get("id"),
        "name": webhook_data.get("name"),
        "channel_id": webhook_data.get("channel_id"),
        "server_id": webhook_data.get("guild_id"),
        "url": webhook_data.get("url"),
        "token": masked_token,  # Security: Only return masked token
        "avatar_url": _get_avatar_url(
            webhook_data.get("id"), webhook_data.get("avatar"), is_webhook=True
        ),
    }


def _get_server_icon_url(server_id: Optional[str], icon_hash: Optional[str]) -> Optional[str]:
    """
    Generate a server icon URL from server ID and icon hash.

    Args:
        server_id: The server/guild ID
        icon_hash: The icon hash from Discord API

    Returns:
        The icon URL or None if no icon exists
    """
    if not server_id or not icon_hash:
        return None

    extension = "png"
    if icon_hash.startswith("a_"):
        extension = "gif"  # Animated icon

    return f"https://cdn.discordapp.com/icons/{server_id}/{icon_hash}.{extension}"


def _get_avatar_url(
    entity_id: Optional[str], avatar_hash: Optional[str], is_webhook: bool = False
) -> Optional[str]:
    """
    Generate an avatar URL from user/webhook ID and avatar hash.

    Args:
        entity_id: The user or webhook ID
        avatar_hash: The avatar hash from Discord API
        is_webhook: Whether this is for a webhook (True) or user (False)

    Returns:
        The avatar URL or None if no avatar exists
    """
    if not entity_id or not avatar_hash:
        return None

    extension = "png"
    if avatar_hash.startswith("a_"):
        extension = "gif"  # Animated avatar

    path = "webhooks" if is_webhook else "avatars"
    return f"https://cdn.discordapp.com/{path}/{entity_id}/{avatar_hash}.{extension}"


def calculate_creation_date(discord_id: str) -> str:
    """Calculate the creation date from a Discord ID (snowflake).

    Args:
        discord_id: A Discord snowflake ID

    Returns:
        ISO-8601 formatted creation date string
    """
    if not discord_id or not discord_id.isdigit():
        return None

    from datetime import datetime, timezone

    # Discord epoch (2015-01-01)
    discord_epoch = 1420070400000
    snowflake = int(discord_id)
    timestamp = ((snowflake >> 22) + discord_epoch) / 1000
    creation_date = datetime.fromtimestamp(timestamp, tz=timezone.utc)

    return creation_date.isoformat()


# ------------------------------------------------------------------------------
# Input Validation Helpers
# ------------------------------------------------------------------------------


def check_required_params(**params) -> None:
    """
    Check that all required parameters are provided and not None.

    Example:
        check_required_params(server_id=server_id, channel_id=channel_id)

    Args:
        **params: Keyword arguments where the key is the parameter name and
                 the value is the parameter value to check

    Raises:
        DiscordValidationError: If any required parameter is None or empty
    """
    for param_name, param_value in params.items():
        if param_value is None or (isinstance(param_value, str) and not param_value.strip()):
            raise DiscordValidationError(
                message=f"{param_name.replace('_', ' ').title()} is required",
                developer_message=f"{param_name} parameter was empty or None",
            )


def check_string_length(value: str, param_name: str, min_length: int, max_length: int) -> None:
    """
    Check that a string parameter has a valid length.

    Example:
        check_string_length(channel_name, "channel_name", 2, 100)

    Args:
        value: The string value to check
        param_name: Name of the parameter (for error messages)
        min_length: Minimum allowed length (inclusive)
        max_length: Maximum allowed length (inclusive)

    Raises:
        DiscordValidationError: If the string length is outside the allowed range
    """
    if not isinstance(value, str):
        raise DiscordValidationError(
            message=f"{param_name.replace('_', ' ').title()} must be a string",
            developer_message=f"{param_name} must be a string, got {type(value)}",
        )

    if len(value) < min_length or len(value) > max_length:
        raise DiscordValidationError(
            message=f"{param_name.replace('_', ' ').title()} must be between {min_length} and {max_length} characters",
            developer_message=f"{param_name} has invalid length: {len(value)}",
        )


def check_numeric_range(
    value: Union[int, float],
    param_name: str,
    min_value: Union[int, float],
    max_value: Union[int, float],
) -> None:
    """
    Check that a numeric parameter is within a valid range.

    Example:
        check_numeric_range(slowmode_timeout, "slowmode_timeout", 0, 21600)

    Args:
        value: The numeric value to check
        param_name: Name of the parameter (for error messages)
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)

    Raises:
        DiscordValidationError: If the value is outside the allowed range
    """
    if not isinstance(value, (int, float)):
        raise DiscordValidationError(
            message=f"{param_name.replace('_', ' ').title()} must be a number",
            developer_message=f"{param_name} must be a number, got {type(value)}",
        )

    if value < min_value or value > max_value:
        raise DiscordValidationError(
            message=f"{param_name.replace('_', ' ').title()} must be between {min_value} and {max_value}",
            developer_message=f"{param_name} has invalid value: {value}",
        )


def validate_embed(embed: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Validate and normalize a Discord message embed.

    Args:
        embed: The embed dictionary to validate

    Returns:
        The validated embed dictionary

    Raises:
        DiscordValidationError: If the embed is invalid
    """
    if embed is None:
        return None

    if not isinstance(embed, dict):
        raise DiscordValidationError(
            message="Embed must be a dictionary",
            developer_message=f"embed must be a dict, got {type(embed)}",
        )

    # Check total embed size constraints
    title = embed.get("title", "")
    description = embed.get("description", "")
    footer = embed.get("footer", {}).get("text", "")
    author = embed.get("author", {}).get("name", "")
    fields = embed.get("fields", [])

    # Calculate approximate character count (Discord has limits)
    char_count = len(title) + len(description) + len(footer) + len(author)
    for field in fields:
        char_count += len(field.get("name", "")) + len(field.get("value", ""))

    if char_count > 6000:
        raise DiscordValidationError(
            message="Embed is too large (exceeds 6000 characters)",
            developer_message=f"Embed total size ({char_count}) exceeds Discord limit of 6000 characters",
        )

    # Check individual field limits
    if title and len(title) > 256:
        raise DiscordValidationError(
            message="Embed title cannot exceed 256 characters",
            developer_message=f"embed.title has invalid length: {len(title)}",
        )

    if description and len(description) > 4096:
        raise DiscordValidationError(
            message="Embed description cannot exceed 4096 characters",
            developer_message=f"embed.description has invalid length: {len(description)}",
        )

    if footer and len(footer) > 2048:
        raise DiscordValidationError(
            message="Embed footer text cannot exceed 2048 characters",
            developer_message=f"embed.footer.text has invalid length: {len(footer)}",
        )

    if author and len(author) > 256:
        raise DiscordValidationError(
            message="Embed author name cannot exceed 256 characters",
            developer_message=f"embed.author.name has invalid length: {len(author)}",
        )

    # Validate fields
    if fields:
        if len(fields) > 25:
            raise DiscordValidationError(
                message="Embed cannot have more than 25 fields",
                developer_message=f"embed.fields has too many items: {len(fields)}",
            )

        for i, field in enumerate(fields):
            field_name = field.get("name", "")
            field_value = field.get("value", "")

            if not field_name:
                raise DiscordValidationError(
                    message=f"Embed field {i + 1} must have a name",
                    developer_message=f"embed.fields[{i}].name is missing or empty",
                )

            if not field_value:
                raise DiscordValidationError(
                    message=f"Embed field {i + 1} must have a value",
                    developer_message=f"embed.fields[{i}].value is missing or empty",
                )

            if len(field_name) > 256:
                raise DiscordValidationError(
                    message=f"Embed field {i + 1} name cannot exceed 256 characters",
                    developer_message=f"embed.fields[{i}].name has invalid length: {len(field_name)}",
                )

            if len(field_value) > 1024:
                raise DiscordValidationError(
                    message=f"Embed field {i + 1} value cannot exceed 1024 characters",
                    developer_message=f"embed.fields[{i}].value has invalid length: {len(field_value)}",
                )

    return embed
