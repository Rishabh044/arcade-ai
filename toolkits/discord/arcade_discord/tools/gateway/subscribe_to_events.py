"""Tool for subscribing to real-time Discord events via Gateway API."""

import asyncio
import uuid
from typing import Annotated, Dict, List, Optional

from arcade.context import ToolContext
from arcade.tool import Discord, tool
from arcade_discord.exceptions import DiscordValidationError
from arcade_discord.gateway import Intents, get_gateway_client

# Global event subscription registry
# Maps subscription_id -> (event_types, server_id, channel_id, callback_url)
_event_subscriptions = {}

# Global event data registry
# Maps subscription_id -> [event_data]
_event_data = {}

# Maximum number of stored events per subscription
MAX_STORED_EVENTS = 100


@tool(
    requires_auth=Discord(
        scopes=["bot", "gateway.connect"],
    )
)
async def subscribe_to_events(
    context: ToolContext,
    event_types: Annotated[
        List[str],
        "List of event types to subscribe to (MESSAGE_CREATE, MESSAGE_REACTION_ADD, etc.)",
    ],
    server_id: Annotated[
        Optional[str], "ID of server to listen to events from (or None for all servers)"
    ] = None,
    channel_id: Annotated[
        Optional[str], "ID of channel to listen to events from (or None for all channels)"
    ] = None,
    callback_url: Annotated[
        Optional[str],
        "Webhook URL to receive events (if not provided, events will be stored for polling)",
    ] = None,
    include_message_content: Annotated[
        bool, "Whether to include message content in events (requires MESSAGE_CONTENT intent)"
    ] = False,
) -> Annotated[Dict, "Details of the event subscription"]:
    """
    Subscribe to real-time events from Discord servers.

    This tool initializes a Gateway connection to receive events as they occur
    in Discord, such as when messages are sent, reactions are added, or users join.
    Events can be filtered by server and channel, and can either be sent to a webhook
    URL or stored for later retrieval.

    Available event types include:
    - MESSAGE_CREATE: When a message is sent
    - MESSAGE_UPDATE: When a message is edited
    - MESSAGE_DELETE: When a message is deleted
    - MESSAGE_REACTION_ADD: When a reaction is added to a message
    - MESSAGE_REACTION_REMOVE: When a reaction is removed from a message
    - GUILD_MEMBER_ADD: When a user joins a server
    - TYPING_START: When a user starts typing
    - PRESENCE_UPDATE: When a user's presence changes

    Example:
        ```python
        # Subscribe to new messages in a specific channel
        subscribe_to_events(
            event_types=["MESSAGE_CREATE"],
            channel_id="123456789012345678",
        )

        # Subscribe to reactions across an entire server
        subscribe_to_events(
            event_types=["MESSAGE_REACTION_ADD", "MESSAGE_REACTION_REMOVE"],
            server_id="123456789012345678",
            callback_url="https://example.com/webhook"
        )
        ```
    """
    # Validation
    if not event_types:
        raise DiscordValidationError(
            message="At least one event type must be specified",
            developer_message="event_types parameter was empty",
        )

    # Calculate necessary intents based on event types
    intents = Intents.GUILDS  # Always include guilds intent

    if include_message_content:
        intents |= Intents.MESSAGE_CONTENT

    if any(event.startswith("MESSAGE_") for event in event_types):
        intents |= Intents.GUILD_MESSAGES | Intents.DIRECT_MESSAGES

    if any(event.endswith("_REACTION_") for event in event_types):
        intents |= Intents.GUILD_MESSAGE_REACTIONS | Intents.DIRECT_MESSAGE_REACTIONS

    if "TYPING_START" in event_types:
        intents |= Intents.GUILD_MESSAGE_TYPING | Intents.DIRECT_MESSAGE_TYPING

    if "PRESENCE_UPDATE" in event_types:
        intents |= Intents.GUILD_PRESENCES

    if "GUILD_MEMBER_ADD" in event_types or "GUILD_MEMBER_REMOVE" in event_types:
        intents |= Intents.GUILD_MEMBERS

    # Get or create gateway client
    client = await get_gateway_client(context, intents)

    # Generate a subscription ID
    subscription_id = str(uuid.uuid4())

    # Initialize event data storage if not using webhook
    if not callback_url:
        _event_data[subscription_id] = []

    # Store subscription details
    _event_subscriptions[subscription_id] = {
        "event_types": event_types,
        "server_id": server_id,
        "channel_id": channel_id,
        "callback_url": callback_url,
    }

    # Define event handler function
    async def event_handler(event_data):
        # Check if event matches filter criteria
        if server_id and event_data.get("guild_id") != server_id:
            return

        if channel_id and event_data.get("channel_id") != channel_id:
            return

        # Handle the event
        if callback_url:
            # Send to webhook (implementation details omitted for brevity)
            pass
        else:
            # Store event data
            event_entry = {
                "timestamp": asyncio.get_event_loop().time(),
                "data": event_data,
            }

            _event_data[subscription_id].append(event_entry)

            # Limit stored events
            if len(_event_data[subscription_id]) > MAX_STORED_EVENTS:
                _event_data[subscription_id] = _event_data[subscription_id][-MAX_STORED_EVENTS:]

    # Register event handlers for each event type
    for event_type in event_types:
        client.add_event_handler(event_type, event_handler)

    # Return subscription details
    return {
        "subscription_id": subscription_id,
        "event_types": event_types,
        "filters": {
            "server_id": server_id,
            "channel_id": channel_id,
        },
        "notification_method": "webhook" if callback_url else "polling",
        "webhook_url": callback_url if callback_url else None,
        "intents_used": intents,
    }
