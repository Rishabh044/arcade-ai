"""Discord toolkit for Arcade AI.

Provides interfaces to Discord services, allowing Arcade AI to interact with
Discord servers, channels, messages, webhooks, and other resources.
"""

# Channel operations
# Import decorator template but don't expose in __all__
import arcade_discord.tools.decorator_template

# Custom types
from arcade_discord.custom_types import (
    Channel,
    ChannelType,
    Embed,
    EmbedAuthor,
    EmbedField,
    EmbedFooter,
    EmbedImage,
    Message,
    Server,
)

# Exceptions
from arcade_discord.exceptions import (
    DiscordAuthError,
    DiscordPermissionError,
    DiscordRateLimitError,
    DiscordRequestError,
    DiscordResourceNotFoundError,
    DiscordToolError,
    DiscordValidationError,
    DiscordWebhookError,
)
from arcade_discord.tools.channels import (
    create_channel,
    create_text_channel,
    get_channel,
    list_channels,
)

# Example tools
from arcade_discord.tools.examples import (
    create_and_post,
    send_formatted_message,
    setup_webhook_integration,
)

# Message operations
from arcade_discord.tools.messages import (
    delete_message,
    edit_message,
    list_messages,
    send_message,
)

# Server operations
from arcade_discord.tools.servers import (
    get_server,
    list_servers,
)

# User operations
from arcade_discord.tools.users import (
    get_current_user,
    get_user,
)

# Webhook operations
from arcade_discord.tools.webhooks import (
    create_webhook,
    list_webhooks,
    send_webhook_message,
)

# Validation utilities
from arcade_discord.validation import (
    validate_channel_name,
    validate_color,
    validate_discord_id,
    validate_embed,
    validate_message_content,
    validate_role_name,
    validate_webhook_url,
)

__all__ = [
    # Channel operations
    "create_channel",
    "create_text_channel",
    "get_channel",
    "list_channels",
    # Message operations
    "delete_message",
    "edit_message",
    "list_messages",
    "send_message",
    # Server operations
    "get_server",
    "list_servers",
    # User operations
    "get_current_user",
    "get_user",
    # Webhook operations
    "create_webhook",
    "list_webhooks",
    "send_webhook_message",
    # Example tools
    "create_and_post",
    "send_formatted_message",
    "setup_webhook_integration",
    # Custom types
    "Channel",
    "ChannelType",
    "Embed",
    "EmbedAuthor",
    "EmbedField",
    "EmbedFooter",
    "EmbedImage",
    "Message",
    "Server",
    # Exceptions
    "DiscordAuthError",
    "DiscordPermissionError",
    "DiscordRateLimitError",
    "DiscordRequestError",
    "DiscordResourceNotFoundError",
    "DiscordToolError",
    "DiscordValidationError",
    "DiscordWebhookError",
    # Validation utilities
    "validate_channel_name",
    "validate_color",
    "validate_discord_id",
    "validate_embed",
    "validate_message_content",
    "validate_role_name",
    "validate_webhook_url",
]
