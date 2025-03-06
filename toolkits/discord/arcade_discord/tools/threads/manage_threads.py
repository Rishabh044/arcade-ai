"""Discord thread management tools.

This module provides tools for creating, managing, and participating in Discord threads,
following Discord's threading model where threads are attached to existing channels.
"""

import logging
from datetime import datetime
from typing import Annotated, Dict, List, Optional

from arcade.core.tool import tool
from arcade.core.tool_context import ToolContext
from arcade.providers.discord import Discord

from ...auth import CHANNEL_SCOPES, MESSAGE_SCOPES
from ...client import get_discord_client
from ...exceptions import (
    DiscordPermissionError,
    DiscordResourceNotFoundError,
    DiscordValidationError,
)

logger = logging.getLogger(__name__)

# Thread types
THREAD_PUBLIC = 11  # Public thread in a text channel
THREAD_PRIVATE = 12  # Private thread in a text channel
THREAD_NEWS = 10  # Thread in an announcement channel
THREAD_FORUM = 11  # Thread in a forum channel

# Thread archive durations (in minutes)
THREAD_ARCHIVE_60 = 60  # 1 hour
THREAD_ARCHIVE_1440 = 1440  # 1 day
THREAD_ARCHIVE_4320 = 4320  # 3 days
THREAD_ARCHIVE_10080 = 10080  # 1 week


@tool(
    requires_auth=Discord(
        scopes=CHANNEL_SCOPES,
    )
)
async def create_thread(
    context: ToolContext,
    channel_id: Annotated[str, "ID of the parent channel to create thread in"],
    name: Annotated[str, "Name of the thread (1-100 characters)"],
    message_id: Annotated[
        Optional[str], "ID of the message to create thread from (required for text channels)"
    ] = None,
    auto_archive_duration: Annotated[
        int, "Minutes until thread auto-archives when inactive (60, 1440, 4320, or 10080)"
    ] = 1440,
    thread_type: Annotated[
        Optional[int], "Type of thread to create (11=public, 12=private, 10=news)"
    ] = None,
    invitable: Annotated[
        bool, "Whether non-moderators can add users to the thread (private threads only)"
    ] = True,
    rate_limit_per_user: Annotated[
        Optional[int], "Slowmode rate limit per user in seconds (0-21600)"
    ] = None,
) -> Annotated[Dict, "Details of the created thread"]:
    """
    Create a new thread in a Discord channel.

    This tool creates different types of threads depending on the channel type and parameters:
    - In text channels: Creates a thread from a message or as a private thread
    - In announcement channels: Creates a thread from an announcement message
    - In forum channels: Creates a forum post (thread)

    Thread types depend on the parent channel:
    - Public threads (11): Standard threads in text channels, visible to everyone
    - Private threads (12): Private threads in text channels, only visible to those invited
    - News threads (10): Threads in announcement channels

    Examples:
    - Create a thread from a specific message to focus discussion
    - Create a private thread for a smaller group conversation
    - Create a thread in a forum channel as a new discussion topic

    Returns a dictionary with complete details of the created thread.
    """
    client = await get_discord_client(context)

    # Get channel details to determine channel type
    try:
        channel = await client.get_channel(channel_id)
        channel_type = channel.get("type")
    except Exception as e:
        logger.error(f"Failed to get channel information: {e!s}")
        raise DiscordResourceNotFoundError(
            message=f"Channel {channel_id} not found or inaccessible",
            developer_message=f"Failed to get channel: {e!s}",
        )

    # Validate the thread name
    if not name or len(name) < 1 or len(name) > 100:
        raise DiscordValidationError(
            message="Thread name must be between 1 and 100 characters",
            developer_message="Invalid thread name length",
        )

    # Validate archive duration
    valid_durations = [
        THREAD_ARCHIVE_60,
        THREAD_ARCHIVE_1440,
        THREAD_ARCHIVE_4320,
        THREAD_ARCHIVE_10080,
    ]
    if auto_archive_duration not in valid_durations:
        raise DiscordValidationError(
            message="auto_archive_duration must be one of 60, 1440, 4320, or 10080 minutes",
            developer_message="Invalid auto_archive_duration",
        )

    # Validate rate limit
    if rate_limit_per_user is not None and (rate_limit_per_user < 0 or rate_limit_per_user > 21600):
        raise DiscordValidationError(
            message="rate_limit_per_user must be between 0 and 21600 seconds",
            developer_message="Invalid rate_limit_per_user",
        )

    thread_data = None

    # Different creation methods based on channel type
    # Text channels (0)
    if channel_type == 0:
        if message_id:
            # Create thread from message
            thread_data = await client.start_thread_with_message(
                channel_id=channel_id,
                message_id=message_id,
                name=name,
                auto_archive_duration=auto_archive_duration,
                rate_limit_per_user=rate_limit_per_user,
            )
        else:
            # Create private thread without message
            if thread_type is None:
                thread_type = THREAD_PRIVATE  # Default to private for text channels

            thread_data = await client.start_thread_without_message(
                channel_id=channel_id,
                name=name,
                auto_archive_duration=auto_archive_duration,
                type=thread_type,
                invitable=invitable,
                rate_limit_per_user=rate_limit_per_user,
            )

    # News/announcement channels (5)
    elif channel_type == 5:
        if not message_id:
            raise DiscordValidationError(
                message="message_id is required for creating threads in announcement channels",
                developer_message="Missing message_id for announcement channel thread",
            )

        thread_data = await client.start_thread_with_message(
            channel_id=channel_id,
            message_id=message_id,
            name=name,
            auto_archive_duration=auto_archive_duration,
            rate_limit_per_user=rate_limit_per_user,
        )

    # Forum channels (15)
    elif channel_type == 15:
        # Create a forum post (thread)
        payload = {
            "name": name,
            "auto_archive_duration": auto_archive_duration,
            "rate_limit_per_user": rate_limit_per_user,
            "message": {
                "content": "Thread created"  # Forum threads require an initial message
            },
        }

        thread_data = await client.start_thread_in_forum(channel_id=channel_id, **payload)

    else:
        raise DiscordValidationError(
            message=f"Cannot create threads in this channel type ({channel_type})",
            developer_message=f"Unsupported channel type for thread creation: {channel_type}",
        )

    # Format response
    return {
        "id": thread_data.get("id"),
        "name": thread_data.get("name"),
        "parent_id": thread_data.get("parent_id"),
        "owner_id": thread_data.get("owner_id"),
        "type": thread_data.get("type"),
        "guild_id": thread_data.get("guild_id"),
        "member_count": thread_data.get("member_count", 0),
        "message_count": thread_data.get("message_count", 0),
        "archived": thread_data.get("thread_metadata", {}).get("archived", False),
        "auto_archive_duration": thread_data.get("thread_metadata", {}).get(
            "auto_archive_duration"
        ),
        "created_at": thread_data.get("thread_metadata", {}).get("create_timestamp"),
    }


@tool(
    requires_auth=Discord(
        scopes=CHANNEL_SCOPES,
    )
)
async def join_thread(
    context: ToolContext,
    thread_id: Annotated[str, "ID of the thread to join"],
) -> Annotated[Dict, "Result of the join operation"]:
    """
    Join a thread in a Discord server.

    This tool allows the bot to join a thread, which is necessary before the bot
    can send messages or read message history in the thread. You should call this
    before attempting to interact with a thread the bot isn't already a member of.

    Examples:
    - Join a thread before sending messages to it
    - Join a private thread after being invited
    - Join an archived thread to revive the conversation

    Returns a dictionary confirming the join operation.
    """
    client = await get_discord_client(context)

    try:
        # Join the thread
        await client.join_thread(thread_id)

        # Get thread details to return
        thread = await client.get_channel(thread_id)

        return {
            "success": True,
            "thread_id": thread_id,
            "thread_name": thread.get("name"),
            "parent_id": thread.get("parent_id"),
            "joined_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to join thread: {e!s}")
        raise DiscordPermissionError(
            message=f"Could not join thread {thread_id}",
            developer_message=f"Failed to join thread: {e!s}",
        )


@tool(
    requires_auth=Discord(
        scopes=CHANNEL_SCOPES,
    )
)
async def archive_thread(
    context: ToolContext,
    thread_id: Annotated[str, "ID of the thread to archive"],
    locked: Annotated[bool, "Whether to lock the thread when archiving"] = False,
) -> Annotated[Dict, "Result of the archive operation"]:
    """
    Archive a Discord thread to hide it from the active threads list.

    This tool archives a thread, which removes it from the active threads list but
    preserves its content. Threads can be unarchived later to continue the discussion.
    You can optionally lock the thread to prevent it from being unarchived by non-moderators.

    Examples:
    - Archive a completed discussion
    - Archive and lock a resolved support request
    - Clean up inactive threads in a channel

    Returns a dictionary confirming the archive operation.
    """
    client = await get_discord_client(context)

    try:
        # Get thread info before archiving
        thread = await client.get_channel(thread_id)

        if thread.get("type") not in [THREAD_PUBLIC, THREAD_PRIVATE, THREAD_NEWS]:
            raise DiscordValidationError(
                message=f"Channel {thread_id} is not a thread",
                developer_message=f"Channel type {thread.get('type')} is not a thread type",
            )

        # Update thread to archive it
        await client.modify_channel(
            channel_id=thread_id,
            archived=True,
            locked=locked,
            reason="Thread archived via Arcade Discord toolkit",
        )

        return {
            "success": True,
            "thread_id": thread_id,
            "thread_name": thread.get("name"),
            "parent_id": thread.get("parent_id"),
            "archived": True,
            "locked": locked,
            "archived_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to archive thread: {e!s}")
        raise DiscordPermissionError(
            message=f"Could not archive thread {thread_id}",
            developer_message=f"Failed to archive thread: {e!s}",
        )


@tool(
    requires_auth=Discord(
        scopes=CHANNEL_SCOPES,
    )
)
async def list_active_threads(
    context: ToolContext,
    server_id: Annotated[str, "ID of the server to list active threads from"],
) -> Annotated[Dict, "List of active threads in the server"]:
    """
    List all active (non-archived) threads in a Discord server.

    This tool retrieves all active threads across all channels in a server, providing
    a comprehensive view of ongoing discussions. The results include details about
    each thread such as name, parent channel, member count, and creation time.

    Examples:
    - Get an overview of all active discussions in a server
    - Find threads that might need moderation attention
    - Locate recent threads a user might be interested in

    Returns a dictionary containing lists of active threads by type (public, private, etc.).
    """
    client = await get_discord_client(context)

    try:
        # Get active threads from the server
        active_threads = await client.list_active_threads(server_id)

        # Format response
        threads = {
            "public_threads": [],
            "private_threads": [],
            "total_count": 0,
        }

        # Process threads by type
        for thread in active_threads.get("threads", []):
            thread_type = thread.get("type")

            thread_info = {
                "id": thread.get("id"),
                "name": thread.get("name"),
                "parent_id": thread.get("parent_id"),
                "owner_id": thread.get("owner_id"),
                "member_count": thread.get("member_count", 0),
                "message_count": thread.get("message_count", 0),
                "created_at": thread.get("thread_metadata", {}).get("create_timestamp"),
                "auto_archive_duration": thread.get("thread_metadata", {}).get(
                    "auto_archive_duration"
                ),
            }

            # Add to appropriate category
            if thread_type == THREAD_PRIVATE:
                threads["private_threads"].append(thread_info)
            else:
                threads["public_threads"].append(thread_info)

        # Update counts
        threads["total_count"] = len(active_threads.get("threads", []))
        threads["public_count"] = len(threads["public_threads"])
        threads["private_count"] = len(threads["private_threads"])

        return threads

    except Exception as e:
        logger.error(f"Failed to list active threads: {e!s}")
        raise DiscordPermissionError(
            message=f"Could not list active threads for server {server_id}",
            developer_message=f"Failed to list active threads: {e!s}",
        )


@tool(
    requires_auth=Discord(
        scopes=CHANNEL_SCOPES + MESSAGE_SCOPES,
    )
)
async def manage_thread_members(
    context: ToolContext,
    thread_id: Annotated[str, "ID of the thread to manage members for"],
    add_members: Annotated[Optional[List[str]], "List of user IDs to add to the thread"] = None,
    remove_members: Annotated[
        Optional[List[str]], "List of user IDs to remove from the thread"
    ] = None,
    send_welcome_message: Annotated[
        bool, "Whether to send a welcome message to newly added members"
    ] = False,
    welcome_message: Annotated[
        Optional[str], "Custom welcome message to send to newly added members"
    ] = None,
) -> Annotated[Dict, "Results of the member management operation"]:
    """
    Add or remove members from a Discord thread.

    This tool allows you to add users to a thread or remove them, which is particularly
    useful for managing private threads where users need explicit invitations to join.
    You can optionally send a welcome message to newly added members.

    Examples:
    - Add support team members to a support thread
    - Remove users from a private thread when they're no longer relevant
    - Invite specific users to a discussion with a welcome message

    Returns a dictionary with results of the addition and removal operations.
    """
    client = await get_discord_client(context)

    # Validate parameters
    if not add_members and not remove_members:
        raise DiscordValidationError(
            message="Must specify at least one member to add or remove",
            developer_message="Both add_members and remove_members are empty or None",
        )

    # Get thread info to validate it's a thread
    try:
        thread = await client.get_channel(thread_id)

        if thread.get("type") not in [THREAD_PUBLIC, THREAD_PRIVATE, THREAD_NEWS]:
            raise DiscordValidationError(
                message=f"Channel {thread_id} is not a thread",
                developer_message=f"Channel type {thread.get('type')} is not a thread type",
            )
    except Exception as e:
        logger.error(f"Failed to get thread information: {e!s}")
        raise DiscordResourceNotFoundError(
            message=f"Thread {thread_id} not found or inaccessible",
            developer_message=f"Failed to get thread: {e!s}",
        )

    results = {
        "thread_id": thread_id,
        "thread_name": thread.get("name"),
        "added_members": [],
        "failed_to_add": [],
        "removed_members": [],
        "failed_to_remove": [],
    }

    # Add members
    if add_members:
        for user_id in add_members:
            try:
                await client.add_thread_member(thread_id, user_id)
                results["added_members"].append(user_id)
            except Exception as e:
                logger.warning(f"Failed to add user {user_id} to thread: {e!s}")
                results["failed_to_add"].append({"user_id": user_id, "error": str(e)})

    # Remove members
    if remove_members:
        for user_id in remove_members:
            try:
                await client.remove_thread_member(thread_id, user_id)
                results["removed_members"].append(user_id)
            except Exception as e:
                logger.warning(f"Failed to remove user {user_id} from thread: {e!s}")
                results["failed_to_remove"].append({"user_id": user_id, "error": str(e)})

    # Send welcome message if requested and members were added
    if send_welcome_message and results["added_members"]:
        try:
            # Default welcome message if none provided
            if not welcome_message:
                added_users = [f"<@{user_id}>" for user_id in results["added_members"]]
                added_mentions = ", ".join(added_users)
                welcome_message = f"Welcome to the thread, {added_mentions}!"

            # Send the message
            message = await client.create_message(channel_id=thread_id, content=welcome_message)

            results["welcome_message_id"] = message.get("id")

        except Exception as e:
            logger.warning(f"Failed to send welcome message: {e!s}")
            results["welcome_message_error"] = str(e)

    # Add summary counts
    results["added_count"] = len(results["added_members"])
    results["removed_count"] = len(results["removed_members"])
    results["failed_to_add_count"] = len(results["failed_to_add"])
    results["failed_to_remove_count"] = len(results["failed_to_remove"])

    return results
