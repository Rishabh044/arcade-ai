"""Tool for executing Discord webhooks."""

from typing import Annotated, Dict, Optional

from discord_webhook import DiscordEmbed, DiscordWebhook

from arcade.context import ToolContext
from arcade.tool import tool
from arcade_discord.exceptions import DiscordToolError, DiscordValidationError, DiscordWebhookError


@tool
async def execute_webhook(
    context: ToolContext,
    webhook_url: Annotated[str, "Complete webhook URL from Discord"],
    content: Annotated[Optional[str], "The text content of the message"] = None,
    username: Annotated[Optional[str], "Override the webhook's default username"] = None,
    avatar_url: Annotated[Optional[str], "Override the webhook's default avatar"] = None,
    embed_title: Annotated[Optional[str], "Title for the embed"] = None,
    embed_description: Annotated[Optional[str], "Description for the embed"] = None,
    embed_color: Annotated[Optional[int], "Color for the embed (hex integer)"] = None,
    tts: Annotated[Optional[bool], "Whether to send as a text-to-speech message"] = False,
) -> Annotated[Dict, "Result of the webhook execution"]:
    """
    Execute a Discord webhook to send a message to a channel.

    This tool sends a message to a Discord channel using a webhook URL. Webhooks are a simple way
    to post messages from external applications without requiring a bot account. You can include
    plain text, customize the sender's name and avatar, and add rich embeds.

    Example:
        ```python
        execute_webhook(
            webhook_url="https://discord.com/api/webhooks/123456789/abcdefg",
            content="Hello from Arcade!",
            username="Arcade Bot",
            embed_title="Important Message",
            embed_description="This is sent via webhook",
            embed_color=0x00ff00
        )
        ```
    """
    # Validation
    if not webhook_url:
        raise DiscordValidationError(
            message="Webhook URL is required",
            developer_message="webhook_url parameter was empty or None",
        )

    if not content and not (embed_title or embed_description):
        raise DiscordValidationError(
            message="Message must include either text content or embed information",
            developer_message="Both content and embed parameters were empty or None",
        )

    try:
        # Create webhook
        webhook = DiscordWebhook(
            url=webhook_url,
            content=content,
            username=username,
            avatar_url=avatar_url,
            tts=tts,
        )

        # Add embed if provided
        if embed_title or embed_description:
            embed = DiscordEmbed(
                title=embed_title,
                description=embed_description,
                color=embed_color,
            )
            webhook.add_embed(embed)

        # Execute webhook
        response = webhook.execute()

        # Check for errors
        if response.status_code >= 400:
            error_message = response.text
            raise DiscordWebhookError(
                message=f"Failed to execute webhook: {error_message}",
                developer_message=f"Webhook error: {error_message} (Code: {response.status_code})",
            )

        return {
            "success": True,
            "status_code": response.status_code,
            "message": "Webhook executed successfully",
        }

    except DiscordToolError:
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        raise DiscordWebhookError(
            message="Failed to execute webhook due to an unexpected error",
            developer_message=f"Error: {e!s}",
        )
