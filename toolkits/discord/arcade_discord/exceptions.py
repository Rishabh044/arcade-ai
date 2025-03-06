"""Discord API exceptions."""

from arcade.exceptions import (
    AuthorizationError,
    RequestError,
    ResourceNotFoundError,
    ToolError,
)


class DiscordToolError(ToolError):
    """Base exception for all Discord tool errors."""


class DiscordAuthError(AuthorizationError):
    """Exception raised for Discord authorization errors."""


class DiscordRequestError(RequestError):
    """Exception raised for errors when making requests to Discord API."""


class DiscordResourceNotFoundError(ResourceNotFoundError):
    """Exception raised when a Discord resource is not found."""


class DiscordRateLimitError(DiscordToolError):
    """Exception raised when Discord API rate limits are hit."""


class DiscordPermissionError(DiscordToolError):
    """Exception raised when user lacks permission for an operation."""


class DiscordValidationError(DiscordToolError):
    """Exception raised when input validation fails."""


class DiscordWebhookError(DiscordToolError):
    """Exception raised for errors related to Discord webhooks."""


class DiscordGatewayError(DiscordToolError):
    """Exception raised for errors related to Discord Gateway API."""


class DiscordInteractionError(DiscordToolError):
    """Exception raised for errors related to Discord interactions."""
