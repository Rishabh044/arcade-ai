"""Validation utilities for Discord-specific parameters."""

import re
from typing import Any, Dict, List, Optional, TypeVar

from arcade_discord.exceptions import DiscordValidationError

T = TypeVar("T")  # Generic type for validation functions that return the input type


def validate_discord_id(
    discord_id: Optional[str], param_name: str, required: bool = True
) -> Optional[str]:
    """Validate a Discord ID (snowflake).

    Args:
        discord_id: Discord ID to validate
        param_name: Parameter name for error messages
        required: Whether parameter is required

    Returns:
        Validated Discord ID or None

    Raises:
        DiscordValidationError: If validation fails
    """
    if discord_id is None:
        if required:
            raise DiscordValidationError(
                message=f"{param_name} is required",
                developer_message=f"{param_name} parameter was None but is required",
            )
        return None

    if not re.match(r"^\d{17,20}$", discord_id):
        raise DiscordValidationError(
            message=f"Invalid {param_name} format",
            developer_message=f"{param_name} must be a numeric string 17-20 characters long, got '{discord_id}'",
        )

    return discord_id


def validate_channel_name(name: str) -> str:
    """Validate and normalize a Discord channel name.

    Args:
        name: Channel name to validate

    Returns:
        Normalized channel name (lowercase with hyphens)

    Raises:
        DiscordValidationError: If validation fails
    """
    if not name:
        raise DiscordValidationError(
            message="Channel name is required",
            developer_message="Channel name parameter was empty or None",
        )

    if len(name) < 2 or len(name) > 100:
        raise DiscordValidationError(
            message="Channel name must be between 2 and 100 characters",
            developer_message=f"Channel name length ({len(name)}) is outside valid range (2-100)",
        )

    # Convert to Discord-compatible format and remove invalid characters
    normalized_name = name.lower().replace(" ", "-")
    normalized_name = re.sub(r"[^a-z0-9_-]", "", normalized_name)

    return normalized_name


def validate_message_content(
    content: Optional[str] = None,
    embed: Optional[Any] = None,
    attachments: Optional[List[Any]] = None,
) -> None:
    """Validate Discord message content.

    Args:
        content: Text content
        embed: Message embed
        attachments: Message attachments

    Raises:
        DiscordValidationError: If validation fails
    """
    # Message must have at least one content type
    if not content and not embed and not (attachments and len(attachments) > 0):
        raise DiscordValidationError(
            message="Message must include content, an embed, or attachments",
            developer_message="No content was provided for the message",
        )

    # Check content length
    if content and len(content) > 2000:
        raise DiscordValidationError(
            message="Message content cannot exceed 2000 characters",
            developer_message=f"Content length ({len(content)}) exceeds maximum (2000)",
        )


def validate_embed(embed: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a Discord message embed.

    Args:
        embed: Embed structure to validate

    Returns:
        Validated embed

    Raises:
        DiscordValidationError: If validation fails
    """
    total_length = 0

    # Title (256 chars)
    if "title" in embed and embed["title"]:
        if len(embed["title"]) > 256:
            raise DiscordValidationError(
                message="Embed title cannot exceed 256 characters",
                developer_message=f"Embed title length ({len(embed['title'])}) exceeds maximum (256)",
            )
        total_length += len(embed["title"])

    # Description (4096 chars)
    if "description" in embed and embed["description"]:
        if len(embed["description"]) > 4096:
            raise DiscordValidationError(
                message="Embed description cannot exceed 4096 characters",
                developer_message=f"Embed description length ({len(embed['description'])}) exceeds maximum (4096)",
            )
        total_length += len(embed["description"])

    # Fields (25 max, name 256 chars, value 1024 chars)
    if "fields" in embed and embed["fields"]:
        if len(embed["fields"]) > 25:
            raise DiscordValidationError(
                message="Embed cannot have more than 25 fields",
                developer_message=f"Embed field count ({len(embed['fields'])}) exceeds maximum (25)",
            )

        for i, field in enumerate(embed["fields"]):
            # Validate field name
            if not field.get("name"):
                raise DiscordValidationError(
                    message="Embed field name is required",
                    developer_message=f"Field {i} is missing required 'name' property",
                )

            if len(field["name"]) > 256:
                raise DiscordValidationError(
                    message="Embed field name cannot exceed 256 characters",
                    developer_message=f"Field {i} name length ({len(field['name'])}) exceeds maximum (256)",
                )

            # Validate field value
            if not field.get("value"):
                raise DiscordValidationError(
                    message="Embed field value is required",
                    developer_message=f"Field {i} is missing required 'value' property",
                )

            if len(field["value"]) > 1024:
                raise DiscordValidationError(
                    message="Embed field value cannot exceed 1024 characters",
                    developer_message=f"Field {i} value length ({len(field['value'])}) exceeds maximum (1024)",
                )

            total_length += len(field["name"]) + len(field["value"])

    # Footer (2048 chars)
    if "footer" in embed and embed["footer"] and "text" in embed["footer"]:
        if len(embed["footer"]["text"]) > 2048:
            raise DiscordValidationError(
                message="Embed footer text cannot exceed 2048 characters",
                developer_message=f"Footer text length ({len(embed['footer']['text'])}) exceeds maximum (2048)",
            )
        total_length += len(embed["footer"]["text"])

    # Author (256 chars)
    if "author" in embed and embed["author"] and "name" in embed["author"]:
        if len(embed["author"]["name"]) > 256:
            raise DiscordValidationError(
                message="Embed author name cannot exceed 256 characters",
                developer_message=f"Author name length ({len(embed['author']['name'])}) exceeds maximum (256)",
            )
        total_length += len(embed["author"]["name"])

    # Total embed limit (6000 chars)
    if total_length > 6000:
        raise DiscordValidationError(
            message="Embed total content cannot exceed 6000 characters",
            developer_message=f"Embed total length ({total_length}) exceeds maximum (6000)",
        )

    return embed


def validate_role_name(name: str) -> str:
    """Validate a Discord role name.

    Args:
        name: Role name to validate

    Returns:
        Validated role name

    Raises:
        DiscordValidationError: If validation fails
    """
    if not name:
        raise DiscordValidationError(
            message="Role name is required",
            developer_message="Role name parameter was empty or None",
        )

    if len(name) > 100:
        raise DiscordValidationError(
            message="Role name cannot exceed 100 characters",
            developer_message=f"Role name length ({len(name)}) exceeds maximum (100)",
        )

    return name


def validate_webhook_url(url: str) -> str:
    """Validate a Discord webhook URL.

    Args:
        url: Webhook URL to validate

    Returns:
        Validated webhook URL

    Raises:
        DiscordValidationError: If validation fails
    """
    if not url:
        raise DiscordValidationError(
            message="Webhook URL is required",
            developer_message="Webhook URL parameter was empty or None",
        )

    webhook_pattern = r"^https://discord\.com/api/webhooks/\d+/[\w-]+$"
    if not re.match(webhook_pattern, url):
        raise DiscordValidationError(
            message="Invalid webhook URL format",
            developer_message="Webhook URL does not match Discord webhook format",
        )

    return url


def validate_color(color: Optional[int]) -> Optional[int]:
    """Validate a Discord color value.

    Args:
        color: Color value to validate (0-16777215)

    Returns:
        Validated color value or None

    Raises:
        DiscordValidationError: If validation fails
    """
    if color is None:
        return None

    if not isinstance(color, int):
        raise DiscordValidationError(
            message="Color must be an integer",
            developer_message=f"Color must be an integer, got {type(color).__name__}",
        )

    if color < 0 or color > 16777215:
        raise DiscordValidationError(
            message="Color must be between 0 and 16777215",
            developer_message=f"Color value ({color}) is outside valid range (0-16777215)",
        )

    return color
