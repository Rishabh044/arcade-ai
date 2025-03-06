"""Tool for sending messages via Discord webhooks.

Webhooks provide a simple way to post messages to Discord channels without requiring
a full bot setup. You can use them for notifications, alerts, and integrations with
external systems.
"""

from typing import Annotated, Dict, List, Optional

from discord_webhook import DiscordEmbed, DiscordWebhook

from arcade.context import ToolContext
from arcade.tool import tool
from arcade_discord.exceptions import DiscordValidationError
from arcade_discord.utils import (
    check_string_length,
    validate_webhook_url,
)


@tool()  # No auth required as webhook URLs contain their own auth
async def send_webhook_message(
    context: ToolContext,
    webhook_url: Annotated[
        str,
        "The full Discord webhook URL to send the message to. Looks like: "
        "'https://discord.com/api/webhooks/123456789012345678/abcdefghijklmnopqrstuvwxyz'. "
        "You can get this URL from Discord by going to Channel Settings > Integrations > Webhooks.",
    ],
    content: Annotated[
        Optional[str],
        "Text content of the message (0-2000 characters). Supports Discord formatting like "
        "**bold**, *italic*, and [hyperlinks](https://example.com). Either content or "
        "at least one embed parameter must be provided.",
    ] = None,
    username: Annotated[
        Optional[str],
        "Custom name to override the webhook's default username (1-80 characters). "
        "Useful for giving context to different types of messages from the same webhook.",
    ] = None,
    avatar_url: Annotated[
        Optional[str],
        "URL to an image to override the webhook's default avatar. Must be a valid image URL "
        "that is publicly accessible (JPG, PNG, or GIF).",
    ] = None,
    embed_title: Annotated[
        Optional[str],
        "Title for the embed (0-256 characters). Appears at the top of the embed in bold text. "
        "Use this for the primary heading of your message.",
    ] = None,
    embed_description: Annotated[
        Optional[str],
        "Main text content for the embed (0-4096 characters). Supports Discord formatting "
        "and appears below the title in regular text.",
    ] = None,
    embed_color: Annotated[
        Optional[str],
        "Color for the embed's left border as a hexadecimal color code (e.g., '#FF0000' for red). "
        "Can be used to indicate priority, category, or status of the message.",
    ] = None,
    embed_fields: Annotated[
        Optional[List[Dict]],
        "List of fields to add to the embed, each a dictionary with 'name', 'value', and optional 'inline' keys. "
        "Fields are displayed as name-value pairs, with 'inline' determining whether fields appear side-by-side. "
        "Example: [{'name': 'Status', 'value': 'Online', 'inline': True}, {'name': 'Region', 'value': 'US East'}]",
    ] = None,
    embed_image_url: Annotated[
        Optional[str],
        "URL to a large image to display in the embed. Must be a publicly accessible image URL. "
        "Images are displayed at their original aspect ratio but may be resized to fit.",
    ] = None,
    embed_thumbnail_url: Annotated[
        Optional[str],
        "URL to a small thumbnail image to display in the upper right of the embed. "
        "Typically square images work best for thumbnails.",
    ] = None,
    embed_footer_text: Annotated[
        Optional[str],
        "Small text to display at the bottom of the embed (0-2048 characters). "
        "Often used for attribution, timestamps, or additional context.",
    ] = None,
) -> Annotated[
    Dict, "Results of the webhook message operation including success status and message ID"
]:
    """
    Send a message to a Discord channel using a webhook URL.

    This tool allows sending messages via Discord webhooks without requiring bot permissions.
    You can send plain text messages or rich embeds with customized appearance.
    The webhook sender's username and avatar can be overridden for each message.

    When to use:
    - When you need to send notifications from external systems to Discord
    - When you want to post updates without requiring a full bot setup
    - When you need to customize the sender's appearance for different message types
    - When you want to create rich, formatted messages with embeds, images, and fields
    - When you need to post alerts or status updates with color coding for severity

    Troubleshooting:
    - Error "Invalid Webhook URL": Verify the webhook URL is correctly copied from Discord
    - Error "Unknown Webhook": The webhook may have been deleted in Discord
    - Error "Cannot send an empty message": Ensure either content or an embed parameter is provided
    - Error "Request entity too large": Your embed content may exceed Discord's size limits
    - Error "Not Found": The channel the webhook was created for may have been deleted

    Examples:
    - Send a simple text notification:
      send_webhook_message(
          webhook_url="https://discord.com/api/webhooks/123456789012345678/token",
          content="The system backup has completed successfully!"
      )

    - Send a notification with custom branding:
      send_webhook_message(
          webhook_url="https://discord.com/api/webhooks/123456789012345678/token",
          content="New user registered: John Smith",
          username="Registration Bot",
          avatar_url="https://example.com/images/registration-icon.png"
      )

    - Send an error alert with color coding and fields:
      send_webhook_message(
          webhook_url="https://discord.com/api/webhooks/123456789012345678/token",
          embed_title="Database Connection Error",
          embed_description="The application lost connection to the primary database.",
          embed_color="#FF0000",
          embed_fields=[
              {"name": "Error Code", "value": "DB-1042", "inline": True},
              {"name": "Severity", "value": "Critical", "inline": True},
              {"name": "Time", "value": "2023-05-20 14:30 UTC", "inline": False},
              {"name": "Affected Services", "value": "User login, payment processing", "inline": False}
          ]
      )

    - Send a status update with thumbnail and footer:
      send_webhook_message(
          webhook_url="https://discord.com/api/webhooks/123456789012345678/token",
          embed_title="System Status: All Systems Operational",
          embed_description="All services are running normally.",
          embed_color="#00FF00",
          embed_thumbnail_url="https://example.com/images/status-green.png",
          embed_footer_text="Updated: May 20, 2023 • Status Page: status.example.com"
      )

    Returns a dictionary containing:
    - success: Whether the message was sent successfully (boolean)
    - message_id: The ID of the sent message if available (string or null)
    - webhook_url: The webhook URL used, partially masked for security (string)
    - status_code: The HTTP status code from the webhook request (integer)
    """
    # Validate the webhook URL
    validate_webhook_url(webhook_url)

    # Validate that either content or an embed is provided
    if not content and not embed_title and not embed_description:
        raise DiscordValidationError(
            message="Message must include either text content or an embed",
            developer_message="No content or embed parameters were provided",
        )

    # Validate content length if provided
    if content:
        check_string_length(content, "content", 0, 2000)

    # Validate username and footer text lengths
    if username:
        check_string_length(username, "username", 1, 80)
    if embed_footer_text:
        check_string_length(embed_footer_text, "embed_footer_text", 0, 2048)

    # Initialize webhook
    webhook = DiscordWebhook(url=webhook_url, content=content)

    # Set custom username and avatar if provided
    if username:
        webhook.username = username
    if avatar_url:
        webhook.avatar_url = avatar_url

    # Create embed if any embed parameters are provided
    if any([
        embed_title,
        embed_description,
        embed_color,
        embed_fields,
        embed_image_url,
        embed_thumbnail_url,
        embed_footer_text,
    ]):
        # Set default color if not provided
        if not embed_color:
            embed_color = "#5865F2"  # Discord brand color
        else:
            # Strip # if provided
            embed_color = embed_color.lstrip("#")

        # Create the embed
        embed = DiscordEmbed(title=embed_title, description=embed_description, color=embed_color)

        # Validate title and description lengths
        if embed_title:
            check_string_length(embed_title, "embed_title", 0, 256)
        if embed_description:
            check_string_length(embed_description, "embed_description", 0, 4096)

        # Add fields if provided
        if embed_fields:
            if len(embed_fields) > 25:
                raise DiscordValidationError(
                    message="Embed cannot have more than 25 fields",
                    developer_message=f"embed_fields has too many items: {len(embed_fields)}",
                )

            for i, field in enumerate(embed_fields):
                name = field.get("name", "")
                value = field.get("value", "")
                inline = field.get("inline", False)

                if not name:
                    raise DiscordValidationError(
                        message=f"Embed field {i + 1} must have a name",
                        developer_message=f"embed_fields[{i}].name is missing or empty",
                    )

                if not value:
                    raise DiscordValidationError(
                        message=f"Embed field {i + 1} must have a value",
                        developer_message=f"embed_fields[{i}].value is missing or empty",
                    )

                check_string_length(name, f"embed_fields[{i}].name", 1, 256)
                check_string_length(value, f"embed_fields[{i}].value", 1, 1024)

                embed.add_embed_field(name=name, value=value, inline=inline)

        # Add images if provided
        if embed_image_url:
            embed.set_image(url=embed_image_url)
        if embed_thumbnail_url:
            embed.set_thumbnail(url=embed_thumbnail_url)

        # Add footer if provided
        if embed_footer_text:
            embed.set_footer(text=embed_footer_text)

        # Add timestamp
        embed.set_timestamp()

        # Add the embed to the webhook
        webhook.add_embed(embed)

    # Execute webhook
    try:
        response = webhook.execute()

        # Mask most of the webhook URL for security
        masked_url = (
            webhook_url[:30] + "..." + webhook_url[-10:] if len(webhook_url) > 40 else webhook_url
        )

        # Check if we got a response (webhook.execute() can return None)
        if response:
            status_code = response.status_code
            success = 200 <= status_code < 300

            # Try to get message ID if possible
            message_id = None
            try:
                if success and hasattr(response, "json"):
                    json_data = response.json()
                    message_id = json_data.get("id")
            except:
                # Ignore errors when trying to parse response
                pass

            return {
                "success": success,
                "message_id": message_id,
                "webhook_url": masked_url,
                "status_code": status_code,
            }
        else:
            # No response usually means success for discord_webhook library
            return {
                "success": True,
                "message_id": None,
                "webhook_url": masked_url,
                "status_code": 204,  # No Content is typical success response
            }
    except Exception as e:
        raise DiscordValidationError(
            message="Failed to send webhook message",
            developer_message=f"Webhook execution error: {e!s}",
        )
