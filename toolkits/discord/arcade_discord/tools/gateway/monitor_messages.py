"""Tool for monitoring Discord messages in real-time using the Gateway API."""

import asyncio
import time
from datetime import datetime
from typing import Annotated, Any, Dict, Optional, Set

from arcade.context import ToolContext
from arcade.tool import Discord, on_delete, tool
from arcade_discord.exceptions import DiscordToolError, DiscordValidationError
from arcade_discord.gateway import GatewayConnection, GatewayIntents
from arcade_discord.utils import MESSAGE_SCOPES, make_discord_request

# Store active monitor sessions
_active_monitors: Dict[str, asyncio.Task] = {}


@tool(
    requires_auth=Discord(
        scopes=MESSAGE_SCOPES,
    )
)
async def monitor_messages(
    context: ToolContext,
    server_id: Annotated[Optional[str], "ID of the server to monitor messages from"] = None,
    channel_id: Annotated[Optional[str], "ID of the channel to monitor messages from"] = None,
    user_id: Annotated[Optional[str], "Filter messages by this user ID"] = None,
    contains_text: Annotated[Optional[str], "Filter messages containing this text"] = None,
    mentions_user: Annotated[Optional[str], "Filter messages that mention this user ID"] = None,
    exclude_bot_messages: Annotated[bool, "Whether to exclude messages from bots"] = False,
    max_messages: Annotated[int, "Maximum number of messages to collect before stopping"] = 100,
    timeout_seconds: Annotated[int, "Maximum time to monitor in seconds"] = 300,
    include_message_updates: Annotated[bool, "Whether to track message updates"] = True,
    include_message_deletes: Annotated[bool, "Whether to track message deletions"] = True,
) -> Annotated[Dict, "Result of the message monitoring operation"]:
    """
    Monitor Discord messages in real-time using Gateway API websocket connections.

    This tool establishes a websocket connection to Discord's Gateway API and listens for
    new messages, message updates, and message deletions based on the specified filters.
    Use this to build notification systems, moderate servers, analyze activity, or record
    conversations.

    The tool will continue monitoring until one of these conditions is met:
    - The maximum number of messages (max_messages) is collected
    - The time limit (timeout_seconds) is reached
    - The tool context is terminated

    Access requires application permissions with MESSAGE_CONTENT intent enabled.

    Examples:
        ```python
        # Monitor all messages in a specific channel
        monitor_messages(channel_id="1234567890123456789", timeout_seconds=120)

        # Monitor messages mentioning a specific user in a server
        monitor_messages(
            server_id="9876543210987654321",
            mentions_user="1111222233334444555",
            exclude_bot_messages=True
        )

        # Monitor messages containing specific text
        monitor_messages(
            server_id="9876543210987654321",
            contains_text="important announcement",
            max_messages=10
        )
        ```
    """
    # Validate input parameters
    if not server_id and not channel_id:
        raise DiscordValidationError(
            message="Either server_id or channel_id must be provided",
            developer_message="Both server_id and channel_id were None or empty",
        )

    if max_messages <= 0:
        raise DiscordValidationError(
            message="max_messages must be a positive integer",
            developer_message=f"Invalid max_messages value: {max_messages}",
        )

    if timeout_seconds <= 0 or timeout_seconds > 3600:
        raise DiscordValidationError(
            message="timeout_seconds must be between 1 and 3600",
            developer_message=f"Invalid timeout_seconds value: {timeout_seconds}",
        )

    # Generate a unique ID for this monitoring session
    session_key = f"{context.request_id}_{time.time()}"

    # Set up data structures to store results
    results = {
        "messages": [],
        "updated_messages": [],
        "deleted_messages": [],
        "stats": {
            "total_collected": 0,
            "new_messages": 0,
            "updated_messages": 0,
            "deleted_messages": 0,
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None,
            "duration_seconds": 0,
        },
    }

    # Set up the collector state
    collector_state = {
        "results": results,
        "max_messages": max_messages,
        "collected_count": 0,
        "message_ids": set(),  # Track message IDs we've seen
        "complete": asyncio.Event(),
        "start_time": time.time(),
    }

    # Create Gateway connection with required intents
    intents = GatewayIntents.default()
    gateway = GatewayConnection(context, intents)

    # Get channels to monitor if server_id was provided
    monitored_channels: Set[str] = set()

    if channel_id:
        monitored_channels.add(channel_id)

    if server_id:
        # Get list of channels in the server
        try:
            channels_response = make_discord_request(
                context=context,
                method="GET",
                endpoint=f"/guilds/{server_id}/channels",
                context_message="get server channels",
            )

            # Add text channels to monitored list
            for channel in channels_response:
                # Filter for text channels (type 0)
                if channel.get("type") == 0:
                    monitored_channels.add(channel.get("id"))
        except Exception as e:
            raise DiscordToolError(
                message="Failed to get channels for server",
                developer_message=f"Error getting channels: {e!s}",
            )

    # Define message handler function
    @gateway.on("MESSAGE_CREATE")
    async def on_message(message_data: Dict[str, Any]) -> None:
        if collector_state["collected_count"] >= max_messages:
            collector_state["complete"].set()
            return

        # Check if message is from a monitored channel
        channel = message_data.get("channel_id")
        if channel not in monitored_channels:
            return

        # Apply filters
        if exclude_bot_messages and message_data.get("author", {}).get("bot", False):
            return

        if user_id and message_data.get("author", {}).get("id") != user_id:
            return

        if contains_text and contains_text.lower() not in message_data.get("content", "").lower():
            return

        if mentions_user:
            mentioned_users = [mention.get("id") for mention in message_data.get("mentions", [])]
            if mentions_user not in mentioned_users:
                return

        # Add message to results
        if message_data.get("id") not in collector_state["message_ids"]:
            collector_state["message_ids"].add(message_data.get("id"))
            collector_state["results"]["messages"].append(message_data)
            collector_state["results"]["stats"]["new_messages"] += 1
            collector_state["collected_count"] += 1
            collector_state["results"]["stats"]["total_collected"] += 1

    # Define message update handler if enabled
    if include_message_updates:

        @gateway.on("MESSAGE_UPDATE")
        async def on_message_update(message_data: Dict[str, Any]) -> None:
            # Check if message is from a monitored channel
            channel = message_data.get("channel_id")
            if channel not in monitored_channels:
                return

            # Apply same filters as for new messages
            if exclude_bot_messages and message_data.get("author", {}).get("bot", False):
                return

            if user_id and message_data.get("author", {}).get("id") != user_id:
                return

            if (
                contains_text
                and contains_text.lower() not in message_data.get("content", "").lower()
            ):
                return

            if mentions_user:
                mentioned_users = [
                    mention.get("id") for mention in message_data.get("mentions", [])
                ]
                if mentions_user not in mentioned_users:
                    return

            # Add to updated messages list
            collector_state["results"]["updated_messages"].append(message_data)
            collector_state["results"]["stats"]["updated_messages"] += 1

            # Count as collected if we haven't seen this message before
            if message_data.get("id") not in collector_state["message_ids"]:
                collector_state["message_ids"].add(message_data.get("id"))
                collector_state["collected_count"] += 1
                collector_state["results"]["stats"]["total_collected"] += 1

    # Define message delete handler if enabled
    if include_message_deletes:

        @gateway.on("MESSAGE_DELETE")
        async def on_message_delete(message_data: Dict[str, Any]) -> None:
            # Check if message is from a monitored channel
            channel = message_data.get("channel_id")
            if channel not in monitored_channels:
                return

            # Add to deleted messages list
            collector_state["results"]["deleted_messages"].append({
                "id": message_data.get("id"),
                "channel_id": message_data.get("channel_id"),
                "guild_id": message_data.get("guild_id"),
                "deleted_at": datetime.utcnow().isoformat(),
            })
            collector_state["results"]["stats"]["deleted_messages"] += 1

    # Define the monitoring task
    async def run_monitoring():
        try:
            # Connect to gateway
            await gateway.connect()

            # Wait for completion
            try:
                # Wait for either max messages or timeout
                done, pending = await asyncio.wait(
                    [
                        asyncio.create_task(collector_state["complete"].wait()),
                        asyncio.create_task(asyncio.sleep(timeout_seconds)),
                    ],
                    return_when=asyncio.FIRST_COMPLETED,
                )

                # Cancel any pending tasks
                for task in pending:
                    task.cancel()

                # Update stats
                end_time = datetime.utcnow()
                collector_state["results"]["stats"]["end_time"] = end_time.isoformat()
                collector_state["results"]["stats"]["duration_seconds"] = (
                    time.time() - collector_state["start_time"]
                )

            finally:
                # Close gateway connection
                await gateway.close()

                # Remove from active monitors
                if session_key in _active_monitors:
                    del _active_monitors[session_key]

            return collector_state["results"]

        except Exception as e:
            # Handle exceptions
            logger_error = f"Error in monitoring task: {e!s}"
            if session_key in _active_monitors:
                del _active_monitors[session_key]
            raise DiscordToolError(
                message="Failed to monitor messages",
                developer_message=logger_error,
            )

    # Start the monitoring task
    monitoring_task = asyncio.create_task(run_monitoring())
    _active_monitors[session_key] = monitoring_task

    try:
        # Wait for the monitoring to complete
        result = await monitoring_task
        return result
    except asyncio.CancelledError:
        # Handle cancellation
        if session_key in _active_monitors:
            del _active_monitors[session_key]

        # Update stats before returning partial results
        end_time = datetime.utcnow()
        collector_state["results"]["stats"]["end_time"] = end_time.isoformat()
        collector_state["results"]["stats"]["duration_seconds"] = (
            time.time() - collector_state["start_time"]
        )

        return collector_state["results"]


@on_delete(monitor_messages)
async def cleanup_monitor(context: ToolContext) -> None:
    """Clean up any active monitoring tasks when the tool is deleted."""
    for session_key, task in list(_active_monitors.items()):
        if not task.done():
            task.cancel()

    _active_monitors.clear()
