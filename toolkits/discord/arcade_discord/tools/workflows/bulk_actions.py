"""Workflow tools for bulk operations in Discord."""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Annotated, Dict, List, Optional

from arcade.context import ToolContext
from arcade.tool import Discord, tool
from arcade_discord.exceptions import DiscordToolError, DiscordValidationError
from arcade_discord.utils import (
    CHANNEL_SCOPES,
    MESSAGE_SCOPES,
    make_discord_request,
)

logger = logging.getLogger(__name__)


@tool(
    requires_auth=Discord(
        scopes=MESSAGE_SCOPES + CHANNEL_SCOPES,
    )
)
async def bulk_delete_messages(
    context: ToolContext,
    channel_id: Annotated[str, "ID of the channel to delete messages from"],
    message_ids: Annotated[Optional[List[str]], "List of specific message IDs to delete"] = None,
    before_id: Annotated[Optional[str], "Delete messages before this message ID"] = None,
    after_id: Annotated[Optional[str], "Delete messages after this message ID"] = None,
    from_user_id: Annotated[Optional[str], "Only delete messages from this user ID"] = None,
    contains_text: Annotated[Optional[str], "Only delete messages containing this text"] = None,
    older_than_days: Annotated[
        Optional[int], "Only delete messages older than this many days"
    ] = None,
    newer_than_days: Annotated[
        Optional[int], "Only delete messages newer than this many days"
    ] = None,
    limit: Annotated[int, "Maximum number of messages to delete"] = 100,
    dry_run: Annotated[
        bool, "If true, only lists the messages that would be deleted without deleting them"
    ] = False,
) -> Annotated[Dict, "Results of the bulk delete operation"]:
    """
    Bulk delete messages from a Discord channel based on various filters.

    This tool first fetches messages matching the specified criteria, then deletes them using
    either the bulk delete API (for messages less than 14 days old) or individual deletion for
    older messages. It provides detailed reporting on the operation's results.

    The `dry_run` parameter can be used to preview which messages would be deleted without
    actually performing the deletion.

    Note: Discord's bulk deletion API only works on messages less than 14 days old.
    Messages older than that will be deleted individually, which is slower.

    Example:
        ```python
        # Delete up to 50 messages containing the word "spam" from a channel
        bulk_delete_messages(
            channel_id="123456789012345678",
            contains_text="spam",
            limit=50
        )

        # Delete messages from a specific user in the last 7 days
        bulk_delete_messages(
            channel_id="123456789012345678",
            from_user_id="876543210987654321",
            newer_than_days=7
        )

        # Preview which messages would be deleted without actually deleting
        bulk_delete_messages(
            channel_id="123456789012345678",
            contains_text="confidential",
            dry_run=True
        )
        ```
    """
    # Validate input parameters
    if not channel_id:
        raise DiscordValidationError(
            message="Channel ID is required",
            developer_message="channel_id parameter was empty or None",
        )

    if limit <= 0 or limit > 1000:
        raise DiscordValidationError(
            message="Limit must be between 1 and 1000",
            developer_message=f"Invalid limit value: {limit}",
        )

    if older_than_days is not None and older_than_days < 0:
        raise DiscordValidationError(
            message="older_than_days must be a positive number",
            developer_message=f"Invalid older_than_days value: {older_than_days}",
        )

    if newer_than_days is not None and newer_than_days < 0:
        raise DiscordValidationError(
            message="newer_than_days must be a positive number",
            developer_message=f"Invalid newer_than_days value: {newer_than_days}",
        )

    # Initialize results
    results = {
        "channel_id": channel_id,
        "messages_found": 0,
        "messages_deleted": 0,
        "bulk_deletion_count": 0,
        "individual_deletion_count": 0,
        "skipped_count": 0,
        "execution_time_seconds": 0,
        "dry_run": dry_run,
        "deleted_messages": [],
        "errors": [],
    }

    start_time = time.time()

    try:
        # Step 1: Build the query parameters for fetching messages
        query_params = {}

        # Add limit
        query_params["limit"] = min(100, limit)  # Discord API limit is 100 per request

        # Add before/after parameters if provided
        if before_id:
            query_params["before"] = before_id

        if after_id:
            query_params["after"] = after_id

        # Step 2: Fetch and filter messages
        all_messages = []
        remaining_limit = limit
        last_id = None

        two_weeks_ago = datetime.utcnow() - timedelta(days=14)

        while remaining_limit > 0:
            # Update query parameters for pagination
            if last_id:
                query_params["before"] = last_id

            # Fetch messages
            messages_response = make_discord_request(
                context=context,
                method="GET",
                endpoint=f"/channels/{channel_id}/messages",
                params=query_params,
                context_message="fetch messages",
            )

            # Break if no more messages
            if not messages_response:
                break

            # Process each message
            for message in messages_response:
                # Check if we've reached the limit
                if len(all_messages) >= limit:
                    break

                # Apply filters
                if from_user_id and message.get("author", {}).get("id") != from_user_id:
                    continue

                if (
                    contains_text
                    and contains_text.lower() not in message.get("content", "").lower()
                ):
                    continue

                # Check specific message IDs if provided
                if message_ids and message.get("id") not in message_ids:
                    continue

                # Check date-based filters if provided
                if message.get("timestamp"):
                    message_time = datetime.fromisoformat(
                        message.get("timestamp").replace("Z", "+00:00")
                    )

                    if older_than_days and message_time > datetime.utcnow() - timedelta(
                        days=older_than_days
                    ):
                        continue

                    if newer_than_days and message_time < datetime.utcnow() - timedelta(
                        days=newer_than_days
                    ):
                        continue

                # Add message to the list
                all_messages.append(message)

            # Update pagination
            if messages_response:
                last_id = messages_response[-1].get("id")
                remaining_limit = limit - len(all_messages)
            else:
                break

        # Update found count
        results["messages_found"] = len(all_messages)

        if dry_run:
            # In dry run mode, just return the messages that would be deleted
            for message in all_messages:
                results["deleted_messages"].append({
                    "id": message.get("id"),
                    "author": {
                        "id": message.get("author", {}).get("id"),
                        "username": message.get("author", {}).get("username"),
                    },
                    "content": message.get("content"),
                    "timestamp": message.get("timestamp"),
                })
        else:
            # Step 3: Perform deletion (for real)
            # Split messages into those eligible for bulk deletion (< 14 days old)
            # and those that need individual deletion

            bulk_delete_ids = []
            individual_delete_ids = []

            for message in all_messages:
                message_id = message.get("id")
                message_time = datetime.fromisoformat(
                    message.get("timestamp").replace("Z", "+00:00")
                )

                # Messages older than 2 weeks need individual deletion
                if message_time < two_weeks_ago:
                    individual_delete_ids.append(message_id)
                else:
                    bulk_delete_ids.append(message_id)

            # Perform bulk deletion if there are eligible messages
            if bulk_delete_ids:
                # Discord bulk delete API has a limit of 100 messages at once
                for i in range(0, len(bulk_delete_ids), 100):
                    batch = bulk_delete_ids[i : i + 100]

                    try:
                        make_discord_request(
                            context=context,
                            method="POST",
                            endpoint=f"/channels/{channel_id}/messages/bulk-delete",
                            json_data={"messages": batch},
                            context_message="bulk delete messages",
                        )

                        # Update stats
                        results["bulk_deletion_count"] += len(batch)
                        results["messages_deleted"] += len(batch)

                        # Log deleted messages
                        for message_id in batch:
                            message = next(
                                (m for m in all_messages if m.get("id") == message_id), None
                            )
                            if message:
                                results["deleted_messages"].append({
                                    "id": message.get("id"),
                                    "author": {
                                        "id": message.get("author", {}).get("id"),
                                        "username": message.get("author", {}).get("username"),
                                    },
                                    "content": message.get("content"),
                                    "timestamp": message.get("timestamp"),
                                    "deletion_method": "bulk",
                                })

                    except Exception as e:
                        error_msg = f"Failed to bulk delete batch: {e!s}"
                        results["errors"].append(error_msg)
                        logger.error(error_msg)

            # Perform individual deletions if needed
            if individual_delete_ids:
                for message_id in individual_delete_ids:
                    try:
                        make_discord_request(
                            context=context,
                            method="DELETE",
                            endpoint=f"/channels/{channel_id}/messages/{message_id}",
                            context_message="delete single message",
                        )

                        # Update stats
                        results["individual_deletion_count"] += 1
                        results["messages_deleted"] += 1

                        # Log deleted message
                        message = next((m for m in all_messages if m.get("id") == message_id), None)
                        if message:
                            results["deleted_messages"].append({
                                "id": message.get("id"),
                                "author": {
                                    "id": message.get("author", {}).get("id"),
                                    "username": message.get("author", {}).get("username"),
                                },
                                "content": message.get("content"),
                                "timestamp": message.get("timestamp"),
                                "deletion_method": "individual",
                            })

                        # Add a small delay to avoid rate limiting
                        await asyncio.sleep(0.25)

                    except Exception as e:
                        error_msg = f"Failed to delete message {message_id}: {e!s}"
                        results["errors"].append(error_msg)
                        logger.error(error_msg)
                        results["skipped_count"] += 1

        # Update execution time
        results["execution_time_seconds"] = time.time() - start_time

        return results

    except Exception as e:
        # Handle unexpected errors
        error_msg = f"Error in bulk delete operation: {e!s}"
        logger.error(error_msg)

        # Update execution time
        results["execution_time_seconds"] = time.time() - start_time
        results["errors"].append(error_msg)

        raise DiscordToolError(
            message="Failed to perform bulk message deletion",
            developer_message=error_msg,
        )


@tool(
    requires_auth=Discord(
        scopes=CHANNEL_SCOPES,
    )
)
async def bulk_update_channels(
    context: ToolContext,
    server_id: Annotated[str, "ID of the server to update channels in"],
    channels: Annotated[List[Dict], "List of channel updates to perform"],
    create_missing: Annotated[bool, "Create channels that don't exist"] = False,
    dry_run: Annotated[
        bool, "If true, only lists the changes that would be made without making them"
    ] = False,
) -> Annotated[Dict, "Results of the bulk channel update operation"]:
    """
    Bulk update multiple Discord channels in a server.

    This tool allows you to update channel properties like name, topic, permission overwrites,
    parent category, and more for multiple channels at once. You can also optionally create
    channels that don't exist.

    The `channels` parameter should be a list of dictionaries, each containing the channel ID
    and the properties to update. For new channels, include a 'name' and 'type' but no 'id'.

    The `dry_run` parameter can be used to preview changes without actually making them.

    Example:
        ```python
        # Update multiple existing channels
        bulk_update_channels(
            server_id="123456789012345678",
            channels=[
                {
                    "id": "111222333444555666",
                    "name": "renamed-channel",
                    "topic": "New topic for this channel"
                },
                {
                    "id": "777888999000111222",
                    "parent_id": "555666777888999000",  # Move to a category
                    "nsfw": True
                }
            ]
        )

        # Create and update channels
        bulk_update_channels(
            server_id="123456789012345678",
            channels=[
                {
                    "id": "111222333444555666",
                    "name": "renamed-channel"
                },
                {
                    "name": "new-channel",  # No ID means create
                    "type": "text",
                    "topic": "A brand new channel"
                }
            ],
            create_missing=True
        )
        ```
    """
    # Validate input parameters
    if not server_id:
        raise DiscordValidationError(
            message="Server ID is required",
            developer_message="server_id parameter was empty or None",
        )

    if not channels or not isinstance(channels, list):
        raise DiscordValidationError(
            message="Channels list is required and must be a list",
            developer_message="channels parameter was empty, None, or not a list",
        )

    # Initialize results
    results = {
        "server_id": server_id,
        "updated_channels": [],
        "created_channels": [],
        "failed_channels": [],
        "skipped_channels": [],
        "dry_run": dry_run,
        "execution_time_seconds": 0,
    }

    start_time = time.time()

    try:
        # First, get all existing channels in the server
        existing_channels = make_discord_request(
            context=context,
            method="GET",
            endpoint=f"/guilds/{server_id}/channels",
            context_message="get server channels",
        )

        existing_channel_ids = {str(channel["id"]): channel for channel in existing_channels}

        # Channel type mapping (string to int)
        type_mapping = {
            "text": 0,
            "voice": 2,
            "category": 4,
            "announcement": 5,
            "forum": 15,
            "stage": 13,
        }

        # Process each channel in the request
        for channel_update in channels:
            channel_id = channel_update.get("id")

            # Clone the update data to avoid modifying the original
            update_data = channel_update.copy()

            # If ID is provided, process as update
            if channel_id:
                # Check if channel exists in this server
                if channel_id not in existing_channel_ids:
                    failure = {
                        "id": channel_id,
                        "action": "update",
                        "error": "Channel not found in server",
                    }
                    results["failed_channels"].append(failure)
                    continue

                # Remove ID from update data as it's in the URL
                if "id" in update_data:
                    del update_data["id"]

                # Convert type from string to int if provided
                if "type" in update_data and isinstance(update_data["type"], str):
                    if update_data["type"].lower() in type_mapping:
                        update_data["type"] = type_mapping[update_data["type"].lower()]
                    else:
                        failure = {
                            "id": channel_id,
                            "action": "update",
                            "error": f"Invalid channel type: {update_data['type']}",
                        }
                        results["failed_channels"].append(failure)
                        continue

                # Skip if no changes
                if not update_data:
                    results["skipped_channels"].append({
                        "id": channel_id,
                        "action": "update",
                        "reason": "No changes specified",
                    })
                    continue

                if dry_run:
                    # In dry run mode, just log what would happen
                    results["updated_channels"].append({
                        "id": channel_id,
                        "action": "update",
                        "changes": update_data,
                        "current": existing_channel_ids[channel_id],
                    })
                else:
                    # Perform the update
                    try:
                        updated_channel = make_discord_request(
                            context=context,
                            method="PATCH",
                            endpoint=f"/channels/{channel_id}",
                            json_data=update_data,
                            context_message="update channel",
                        )

                        results["updated_channels"].append({
                            "id": updated_channel["id"],
                            "name": updated_channel["name"],
                            "type": updated_channel["type"],
                            "action": "update",
                            "success": True,
                        })
                    except Exception as e:
                        failure = {"id": channel_id, "action": "update", "error": str(e)}
                        results["failed_channels"].append(failure)

            # If no ID but create_missing is True, process as create
            elif create_missing:
                # Ensure required fields are present
                if "name" not in update_data:
                    failure = {"action": "create", "error": "Name is required for new channels"}
                    results["failed_channels"].append(failure)
                    continue

                # Convert type from string to int if provided
                if "type" in update_data and isinstance(update_data["type"], str):
                    if update_data["type"].lower() in type_mapping:
                        update_data["type"] = type_mapping[update_data["type"].lower()]
                    else:
                        failure = {
                            "name": update_data.get("name"),
                            "action": "create",
                            "error": f"Invalid channel type: {update_data['type']}",
                        }
                        results["failed_channels"].append(failure)
                        continue
                elif "type" not in update_data:
                    # Default to text channel
                    update_data["type"] = 0

                if dry_run:
                    # In dry run mode, just log what would happen
                    results["created_channels"].append({"action": "create", "data": update_data})
                else:
                    # Perform the creation
                    try:
                        created_channel = make_discord_request(
                            context=context,
                            method="POST",
                            endpoint=f"/guilds/{server_id}/channels",
                            json_data=update_data,
                            context_message="create channel",
                        )

                        results["created_channels"].append({
                            "id": created_channel["id"],
                            "name": created_channel["name"],
                            "type": created_channel["type"],
                            "action": "create",
                            "success": True,
                        })
                    except Exception as e:
                        failure = {
                            "name": update_data.get("name"),
                            "action": "create",
                            "error": str(e),
                        }
                        results["failed_channels"].append(failure)

            # Skip if no ID and create_missing is False
            else:
                results["skipped_channels"].append({
                    "action": "create",
                    "data": update_data,
                    "reason": "create_missing is False",
                })

        # Update execution time
        results["execution_time_seconds"] = time.time() - start_time

        return results

    except Exception as e:
        # Handle unexpected errors
        error_msg = f"Error in bulk channel update operation: {e!s}"
        logger.error(error_msg)

        # Update execution time
        results["execution_time_seconds"] = time.time() - start_time

        raise DiscordToolError(
            message="Failed to perform bulk channel updates",
            developer_message=error_msg,
        )
