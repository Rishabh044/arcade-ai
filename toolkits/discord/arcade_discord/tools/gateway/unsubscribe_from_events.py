"""Tool for unsubscribing from Discord Gateway events."""

from typing import Annotated, Dict

from arcade.context import ToolContext
from arcade.tool import tool
from arcade_discord.exceptions import DiscordValidationError

# Import the subscription registries from subscribe_to_events
from .subscribe_to_events import _event_data, _event_subscriptions


@tool
async def unsubscribe_from_events(
    context: ToolContext,
    subscription_id: Annotated[str, "ID of the event subscription to cancel"],
) -> Annotated[Dict, "Result of the unsubscribe operation"]:
    """
    Unsubscribe from Discord Gateway events.

    This tool cancels an existing event subscription created with subscribe_to_events.
    Any stored events for this subscription will be deleted.

    Example:
        ```python
        unsubscribe_from_events(subscription_id="123e4567-e89b-12d3-a456-426614174000")
        ```
    """
    # Validation
    if not subscription_id:
        raise DiscordValidationError(
            message="Subscription ID is required",
            developer_message="subscription_id parameter was empty or None",
        )

    # Check if subscription exists
    if subscription_id not in _event_subscriptions:
        raise DiscordValidationError(
            message=f"Subscription with ID {subscription_id} not found",
            developer_message=f"Invalid subscription_id: {subscription_id}",
        )

    # Get subscription details before removing
    subscription = _event_subscriptions[subscription_id]

    # Remove subscription
    del _event_subscriptions[subscription_id]

    # Remove stored events if any
    if subscription_id in _event_data:
        del _event_data[subscription_id]

    # Return success result
    return {
        "success": True,
        "subscription_id": subscription_id,
        "message": "Successfully unsubscribed from events",
        "unsubscribed_events": subscription["event_types"],
    }
