"""Tool for creating webhooks to receive Discord Gateway events."""

import time
from typing import Annotated, Dict, List, Optional

from arcade.context import ToolContext
from arcade.tool import Discord, tool
from arcade_discord.exceptions import DiscordToolError, DiscordValidationError
from arcade_discord.utils import SERVER_SCOPES, make_discord_request


@tool(
    requires_auth=Discord(
        scopes=SERVER_SCOPES,
    )
)
async def register_gateway_webhook(
    context: ToolContext,
    webhook_url: Annotated[str, "URL of the webhook to receive Discord events"],
    server_id: Annotated[str, "ID of the server to monitor"],
    events: Annotated[List[str], "List of event types to subscribe to"],
    include_message_content: Annotated[bool, "Whether to include message content in events"] = True,
    description: Annotated[Optional[str], "Description of this webhook subscription"] = None,
) -> Annotated[Dict, "Information about the registered webhook"]:
    """
    Register a webhook to receive Discord Gateway events.

    This tool creates an integration between Discord and your webhook endpoint to receive
    real-time events from a Discord server. When events you've subscribed to occur (like
    new messages, reactions, or member joins), Discord will send HTTP requests to your
    webhook URL with event data.

    Webhook URLs must use HTTPS and respond to Discord's validation requests. To receive
    message content, your bot must have the Message Content intent enabled and the
    include_message_content parameter must be set to True.

    Examples:
    - Create a webhook to forward all new messages to an external system
    - Set up event monitoring for member joins/leaves for analytics
    - Create a logging system that captures message edits and deletions
    - Build an integration that reacts to emoji reactions on messages

    Returns a dictionary containing:
    - webhook_id: Unique identifier for the webhook
    - name: Name of the webhook (derived from your bot)
    - server_id: ID of the monitored server
    - events: List of events being subscribed to
    - token: Secret token for webhook management (keep secure)
    """
    # Validate input parameters
    if not webhook_url:
        raise DiscordValidationError(
            message="Webhook URL is required",
            developer_message="webhook_url parameter was empty or None",
        )

    if not webhook_url.startswith("https://"):
        raise DiscordValidationError(
            message="Webhook URL must use HTTPS",
            developer_message="Insecure webhook URL provided",
        )

    if not server_id:
        raise DiscordValidationError(
            message="Server ID is required",
            developer_message="server_id parameter was empty or None",
        )

    if not events or not isinstance(events, list) or len(events) == 0:
        raise DiscordValidationError(
            message="At least one event type must be specified",
            developer_message="events parameter was empty, None, or not a list",
        )

    # Valid event types
    valid_events = {
        "MESSAGE_CREATE",
        "MESSAGE_UPDATE",
        "MESSAGE_DELETE",
        "GUILD_MEMBER_ADD",
        "GUILD_MEMBER_REMOVE",
        "GUILD_MEMBER_UPDATE",
        "GUILD_ROLE_CREATE",
        "GUILD_ROLE_UPDATE",
        "GUILD_ROLE_DELETE",
        "CHANNEL_CREATE",
        "CHANNEL_UPDATE",
        "CHANNEL_DELETE",
        "REACTION_ADD",
        "REACTION_REMOVE",
        "GUILD_BAN_ADD",
        "GUILD_BAN_REMOVE",
        "VOICE_STATE_UPDATE",
        "TYPING_START",
    }

    # Check if all events are valid
    invalid_events = [event for event in events if event not in valid_events]
    if invalid_events:
        raise DiscordValidationError(
            message=f"Invalid event types: {', '.join(invalid_events)}",
            developer_message=f"Invalid event types in request: {invalid_events}",
        )

    try:
        # First, get the current server webhooks (if any)
        existing_webhooks = make_discord_request(
            context=context,
            method="GET",
            endpoint=f"/guilds/{server_id}/webhooks",
            context_message="get server webhooks",
        )

        # Create webhook configuration
        webhook_data = {
            "name": f"Gateway-{int(time.time())}",
            "url": webhook_url,
            "type": 1,  # Incoming webhook type
            "description": description or f"Gateway webhook for {', '.join(events)}",
            "subscriptions": [{"type": event} for event in events],
        }

        if include_message_content:
            webhook_data["message_content"] = True

        # Create the webhook
        response = make_discord_request(
            context=context,
            method="POST",
            endpoint=f"/guilds/{server_id}/webhooks",
            json_data=webhook_data,
            context_message="create gateway webhook",
        )

        # Format the response
        webhook_info = {
            "id": response.get("id"),
            "name": response.get("name"),
            "server_id": server_id,
            "events": events,
            "includes_message_content": include_message_content,
            "creation_time": int(time.time()),
            "status": "active",
            "token": response.get("token"),  # Token for managing this webhook
            "url": f"https://discord.com/api/webhooks/{response.get('id')}/{response.get('token')}",
        }

        return webhook_info

    except Exception as e:
        error_msg = f"Failed to register webhook: {e!s}"
        raise DiscordToolError(
            message="Failed to register webhook for Gateway events",
            developer_message=error_msg,
        )


@tool(
    requires_auth=Discord(
        scopes=SERVER_SCOPES,
    )
)
async def list_gateway_webhooks(
    context: ToolContext,
    server_id: Annotated[str, "ID of the server to get webhooks for"],
) -> Annotated[Dict, "Information about the server's webhooks"]:
    """
    List all webhooks configured for a Discord server.

    This tool retrieves all webhook integrations set up for the specified server,
    including their IDs, names, and types. Use this to manage your existing
    webhooks before creating new ones.

    Example:
        ```python
        list_gateway_webhooks(server_id="123456789012345678")
        ```
    """
    # Validate input parameters
    if not server_id:
        raise DiscordValidationError(
            message="Server ID is required",
            developer_message="server_id parameter was empty or None",
        )

    try:
        # Get all webhooks for the server
        webhooks = make_discord_request(
            context=context,
            method="GET",
            endpoint=f"/guilds/{server_id}/webhooks",
            context_message="get server webhooks",
        )

        # Format the response
        formatted_webhooks = []

        for webhook in webhooks:
            formatted_webhook = {
                "id": webhook.get("id"),
                "name": webhook.get("name"),
                "type": webhook.get("type"),
                "channel_id": webhook.get("channel_id"),
                "application_id": webhook.get("application_id"),
                "url": f"https://discord.com/api/webhooks/{webhook.get('id')}/{webhook.get('token')}"
                if webhook.get("token")
                else None,
            }

            formatted_webhooks.append(formatted_webhook)

        return {
            "server_id": server_id,
            "webhook_count": len(formatted_webhooks),
            "webhooks": formatted_webhooks,
        }

    except Exception as e:
        error_msg = f"Failed to list webhooks: {e!s}"
        raise DiscordToolError(
            message="Failed to retrieve Gateway webhooks",
            developer_message=error_msg,
        )


@tool(
    requires_auth=Discord(
        scopes=SERVER_SCOPES,
    )
)
async def delete_gateway_webhook(
    context: ToolContext,
    webhook_id: Annotated[str, "ID of the webhook to delete"],
    server_id: Annotated[Optional[str], "ID of the server the webhook belongs to"] = None,
) -> Annotated[Dict, "Result of the webhook deletion"]:
    """
    Delete a Discord webhook by its ID.

    This tool removes a webhook integration from Discord. Once deleted, the webhook
    will no longer receive events. This action cannot be undone.

    Example:
        ```python
        delete_gateway_webhook(webhook_id="123456789012345678")
        ```
    """
    # Validate input parameters
    if not webhook_id:
        raise DiscordValidationError(
            message="Webhook ID is required",
            developer_message="webhook_id parameter was empty or None",
        )

    try:
        # Endpoint to use
        endpoint = f"/webhooks/{webhook_id}"

        # Delete the webhook
        make_discord_request(
            context=context,
            method="DELETE",
            endpoint=endpoint,
            context_message="delete webhook",
        )

        # Return success response
        return {
            "webhook_id": webhook_id,
            "server_id": server_id,
            "deleted": True,
            "timestamp": int(time.time()),
        }

    except Exception as e:
        error_msg = f"Failed to delete webhook: {e!s}"
        raise DiscordToolError(
            message="Failed to delete Gateway webhook",
            developer_message=error_msg,
        )
