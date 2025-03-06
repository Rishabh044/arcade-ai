"""Discord moderation workflow tools.

This module provides high-level tools for moderation workflows in Discord,
combining multiple actions like warning, timeout, ban, and logging into
streamlined operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Annotated, Dict, List, Optional

from arcade.core.tool import tool
from arcade.core.tool_context import ToolContext
from arcade.providers.discord import Discord

from ...auth import BAN_SCOPES, CHANNEL_SCOPES, MEMBER_SCOPES, MESSAGE_SCOPES, SERVER_SCOPES
from ...client import get_discord_client
from ...exceptions import DiscordValidationError

logger = logging.getLogger(__name__)

# Moderation action types
ACTION_WARN = "warn"
ACTION_TIMEOUT = "timeout"
ACTION_KICK = "kick"
ACTION_BAN = "ban"
ACTION_UNBAN = "unban"
ACTION_REMOVE_TIMEOUT = "remove_timeout"


# Validation helpers
def validate_duration(hours: Optional[int], days: Optional[int]) -> None:
    """Validate timeout duration."""
    if hours is not None and (hours < 0 or hours > 336):  # Max 14 days (336 hours)
        raise DiscordValidationError(
            message="Timeout hours must be between 0 and 336 (14 days)",
            developer_message="Discord timeout maximum is 14 days (336 hours)",
        )

    if days is not None and (days < 0 or days > 14):  # Max 14 days
        raise DiscordValidationError(
            message="Timeout days must be between 0 and 14",
            developer_message="Discord timeout maximum is 14 days",
        )


@tool(
    requires_auth=Discord(
        scopes=MEMBER_SCOPES + MESSAGE_SCOPES + CHANNEL_SCOPES,
    )
)
async def moderate_user(
    context: ToolContext,
    server_id: Annotated[str, "ID of the server where moderation action will be taken"],
    user_id: Annotated[str, "ID of the user to take action against"],
    action: Annotated[
        str, "Moderation action to take: warn, timeout, kick, ban, unban, or remove_timeout"
    ],
    reason: Annotated[str, "Reason for the moderation action"],
    log_channel_id: Annotated[
        Optional[str], "ID of channel where moderation action should be logged"
    ] = None,
    dm_notification: Annotated[bool, "Whether to send the user a DM about the action"] = True,
    timeout_hours: Annotated[
        Optional[int], "Hours to timeout the user (up to 336 hours / 14 days)"
    ] = None,
    timeout_days: Annotated[Optional[int], "Days to timeout the user (up to 14 days)"] = None,
    delete_message_days: Annotated[
        int, "Number of days of message history to delete when banning (0-7)"
    ] = 0,
    include_warning_history: Annotated[
        bool, "Whether to include previous moderation actions against this user in log"
    ] = True,
) -> Annotated[Dict, "Details of the moderation action taken"]:
    """
    Take a moderation action against a user with optional logging and notification.

    This tool combines multiple moderation actions into a single workflow:
    1. Take the requested action (warn, timeout, kick, ban, unban, remove timeout)
    2. Send a DM notification to the user if requested
    3. Log the action to the specified channel
    4. Return comprehensive information about the action taken

    Examples:
    - Warn a user for rule violation and log it to the mod channel
    - Timeout a user for 24 hours with DM notification and logging
    - Ban a user, delete 7 days of messages, notify them, and log the action

    Returns a dictionary with:
    - action_details: Information about the action taken
    - user_details: Information about the moderated user
    - notification_sent: Whether DM was sent successfully
    - log_message_id: ID of the message posted to the log channel
    """
    client = await get_discord_client(context)

    # Validate inputs
    if action not in [
        ACTION_WARN,
        ACTION_TIMEOUT,
        ACTION_KICK,
        ACTION_BAN,
        ACTION_UNBAN,
        ACTION_REMOVE_TIMEOUT,
    ]:
        raise DiscordValidationError(
            message=f"Invalid action: {action}. Must be one of: warn, timeout, kick, ban, unban, remove_timeout",
            developer_message=f"Invalid moderation action: {action}",
        )

    if action == ACTION_TIMEOUT or action == ACTION_REMOVE_TIMEOUT:
        validate_duration(timeout_hours, timeout_days)

    if action == ACTION_BAN and (delete_message_days < 0 or delete_message_days > 7):
        raise DiscordValidationError(
            message="delete_message_days must be between 0 and 7",
            developer_message="Discord API limits message deletion on ban to 7 days",
        )

    # Fetch user info before action
    try:
        member = await client.get_guild_member(server_id, user_id)
        user = {
            "id": user_id,
            "username": member.get("user", {}).get("username", "Unknown"),
            "discriminator": member.get("user", {}).get("discriminator", "0000"),
            "joined_at": member.get("joined_at"),
        }
    except Exception as e:
        # For unban, the user might not be in the server
        if action != ACTION_UNBAN:
            logger.warning(f"Could not fetch member data for {user_id}: {e!s}")

        # Try to get basic user info
        try:
            user_data = await client.get_user(user_id)
            user = {
                "id": user_id,
                "username": user_data.get("username", "Unknown"),
                "discriminator": user_data.get("discriminator", "0000"),
            }
        except Exception:
            user = {"id": user_id, "username": "Unknown", "discriminator": "0000"}

    # Perform the requested action
    action_details = {}
    timestamp = datetime.utcnow().isoformat()

    if action == ACTION_WARN:
        # Warning is just a log entry, no API action needed
        action_details = {
            "type": "warning",
            "timestamp": timestamp,
            "reason": reason,
        }

    elif action == ACTION_TIMEOUT:
        # Calculate timeout duration
        timeout_duration = timedelta()
        if timeout_hours:
            timeout_duration += timedelta(hours=timeout_hours)
        if timeout_days:
            timeout_duration += timedelta(days=timeout_days)

        # Default to 1 hour if no duration specified
        if timeout_duration == timedelta():
            timeout_duration = timedelta(hours=1)

        timeout_until = datetime.utcnow() + timeout_duration
        iso_timestamp = timeout_until.isoformat()

        await client.modify_guild_member(
            server_id, user_id, communication_disabled_until=iso_timestamp, reason=reason
        )

        action_details = {
            "type": "timeout",
            "timestamp": timestamp,
            "reason": reason,
            "duration": str(timeout_duration),
            "expires_at": iso_timestamp,
        }

    elif action == ACTION_REMOVE_TIMEOUT:
        await client.modify_guild_member(
            server_id, user_id, communication_disabled_until=None, reason=reason
        )

        action_details = {
            "type": "timeout_removed",
            "timestamp": timestamp,
            "reason": reason,
        }

    elif action == ACTION_KICK:
        await client.remove_guild_member(server_id, user_id, reason=reason)

        action_details = {
            "type": "kick",
            "timestamp": timestamp,
            "reason": reason,
        }

    elif action == ACTION_BAN:
        await client.create_guild_ban(
            server_id, user_id, delete_message_days=delete_message_days, reason=reason
        )

        action_details = {
            "type": "ban",
            "timestamp": timestamp,
            "reason": reason,
            "message_days_deleted": delete_message_days,
        }

    elif action == ACTION_UNBAN:
        await client.remove_guild_ban(server_id, user_id, reason=reason)

        action_details = {
            "type": "unban",
            "timestamp": timestamp,
            "reason": reason,
        }

    # Send DM notification if requested
    notification_sent = False
    if dm_notification:
        try:
            # Create DM channel
            dm_channel = await client.create_dm(user_id)
            dm_channel_id = dm_channel.get("id")

            # Format user-friendly message based on action
            action_msg = {
                ACTION_WARN: "**Warning**",
                ACTION_TIMEOUT: f"**Timeout** for {action_details.get('duration', 'some time')}",
                ACTION_KICK: "**Kick**",
                ACTION_BAN: "**Ban**",
                ACTION_UNBAN: "**Unban**",
                ACTION_REMOVE_TIMEOUT: "**Timeout Removed**",
            }.get(action, "Moderation action")

            server = await client.get_guild(server_id)
            server_name = server.get("name", "the server")

            message = f"{action_msg} from {server_name}\n\n**Reason:** {reason}"

            # Send the DM
            await client.create_message(dm_channel_id, content=message)
            notification_sent = True

        except Exception as e:
            logger.warning(f"Failed to send DM notification: {e!s}")
            # Continue even if DM fails

    # Log to moderation channel if requested
    log_message_id = None
    if log_channel_id:
        try:
            # Get user history if requested
            history = []
            if include_warning_history:
                # This would normally come from your database
                # For now, we'll return an empty list
                pass

            # Create an embed for the log
            embed = {
                "title": f"Moderation Action: {action.upper()}",
                "color": {
                    ACTION_WARN: 16776960,  # Yellow
                    ACTION_TIMEOUT: 16753920,  # Orange
                    ACTION_KICK: 15158332,  # Red
                    ACTION_BAN: 10038562,  # Dark Red
                    ACTION_UNBAN: 3066993,  # Green
                    ACTION_REMOVE_TIMEOUT: 3447003,  # Blue
                }.get(action, 3447003),  # Default blue
                "fields": [
                    {
                        "name": "User",
                        "value": f"<@{user_id}> ({user['username']}#{user['discriminator']})",
                        "inline": True,
                    },
                    {"name": "Moderator", "value": f"<@{context.user_id}>", "inline": True},
                    {"name": "Reason", "value": reason, "inline": False},
                ],
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Add action-specific fields
            if action == ACTION_TIMEOUT:
                embed["fields"].append({
                    "name": "Duration",
                    "value": action_details.get("duration", "Unknown"),
                    "inline": True,
                })
                embed["fields"].append({
                    "name": "Expires At",
                    "value": action_details.get("expires_at", "Unknown"),
                    "inline": True,
                })

            elif action == ACTION_BAN:
                embed["fields"].append({
                    "name": "Message History Deleted",
                    "value": f"{delete_message_days} days",
                    "inline": True,
                })

            # Add prior history if available
            if history:
                history_text = "\n".join([
                    f"• {h['type']} - {h['reason']} ({h['timestamp']})"
                    for h in history[:5]  # Show up to 5 most recent actions
                ])

                if len(history) > 5:
                    history_text += f"\n...and {len(history) - 5} more actions"

                embed["fields"].append({
                    "name": "Prior History",
                    "value": history_text,
                    "inline": False,
                })

            # Send log message
            log_message = await client.create_message(
                log_channel_id,
                content=f"Moderation action: {action.upper()} | User: <@{user_id}>",
                embeds=[embed],
            )

            log_message_id = log_message.get("id")

        except Exception as e:
            logger.warning(f"Failed to log moderation action: {e!s}")
            # Continue even if logging fails

    # Return comprehensive result
    return {
        "success": True,
        "action_details": action_details,
        "user_details": user,
        "notification_sent": notification_sent,
        "log_message_id": log_message_id,
        "server_id": server_id,
    }


@tool(
    requires_auth=Discord(
        scopes=BAN_SCOPES + SERVER_SCOPES,
    )
)
async def bulk_enforce_moderation(
    context: ToolContext,
    server_id: Annotated[str, "ID of the server to enforce moderation on"],
    enforcement_actions: Annotated[
        List[Dict],
        "List of moderation actions to take, each with user_id, action, and reason fields",
    ],
    log_channel_id: Annotated[
        Optional[str], "ID of channel where all moderation actions should be logged"
    ] = None,
    dm_notification: Annotated[bool, "Whether to send DM notifications to affected users"] = True,
    dry_run: Annotated[
        bool, "If true, only lists the actions that would be taken without executing them"
    ] = False,
) -> Annotated[Dict, "Results of the bulk moderation actions"]:
    """
    Enforce multiple moderation actions in bulk.

    This tool allows you to apply moderation actions to multiple users at once,
    which is useful for handling raid situations or enforcing rules against groups
    of users who violated server policies.

    Each enforcement action in the list should be a dictionary with:
    - user_id: ID of the user to take action against
    - action: One of 'warn', 'timeout', 'kick', 'ban', 'unban', 'remove_timeout'
    - reason: Reason for the moderation action
    - timeout_days: (Optional) For timeout actions, days to timeout
    - timeout_hours: (Optional) For timeout actions, hours to timeout
    - delete_message_days: (Optional) For ban actions, days of message history to delete

    Examples:
    - Ban multiple users involved in a raid
    - Issue warnings to users breaking a specific rule
    - Remove timeouts from a group of users after a cooling period

    Returns a dictionary with successful actions, failed actions, and counts.
    """
    if not enforcement_actions:
        raise DiscordValidationError(
            message="No enforcement actions provided",
            developer_message="enforcement_actions list is empty",
        )

    results = {
        "successful_actions": [],
        "failed_actions": [],
        "dry_run": dry_run,
        "server_id": server_id,
        "log_channel_id": log_channel_id,
        "total_actions": len(enforcement_actions),
    }

    # In dry run mode, just validate and return the actions
    if dry_run:
        for action in enforcement_actions:
            user_id = action.get("user_id")
            action_type = action.get("action")
            reason = action.get("reason")

            if not user_id or not action_type or not reason:
                results["failed_actions"].append({
                    "user_id": user_id,
                    "action": action_type,
                    "reason": reason,
                    "error": "Missing required fields: user_id, action, and reason are required",
                })
                continue

            if action_type not in [
                ACTION_WARN,
                ACTION_TIMEOUT,
                ACTION_KICK,
                ACTION_BAN,
                ACTION_UNBAN,
                ACTION_REMOVE_TIMEOUT,
            ]:
                results["failed_actions"].append({
                    "user_id": user_id,
                    "action": action_type,
                    "reason": reason,
                    "error": f"Invalid action type: {action_type}",
                })
                continue

            results["successful_actions"].append({
                "user_id": user_id,
                "action": action_type,
                "reason": reason,
                "would_execute": True,
            })

        return results

    # Actually execute the actions
    for action in enforcement_actions:
        user_id = action.get("user_id")
        action_type = action.get("action")
        reason = action.get("reason")

        # Extract action-specific parameters
        timeout_hours = action.get("timeout_hours")
        timeout_days = action.get("timeout_days")
        delete_message_days = action.get("delete_message_days", 0)

        try:
            # Call moderate_user for each action
            result = await moderate_user(
                context=context,
                server_id=server_id,
                user_id=user_id,
                action=action_type,
                reason=reason,
                log_channel_id=log_channel_id,
                dm_notification=dm_notification,
                timeout_hours=timeout_hours,
                timeout_days=timeout_days,
                delete_message_days=delete_message_days,
            )

            results["successful_actions"].append({
                "user_id": user_id,
                "action": action_type,
                "reason": reason,
                "result": result,
            })

        except Exception as e:
            error_message = str(e)
            results["failed_actions"].append({
                "user_id": user_id,
                "action": action_type,
                "reason": reason,
                "error": error_message,
            })

    # Add summary statistics
    results["success_count"] = len(results["successful_actions"])
    results["failure_count"] = len(results["failed_actions"])

    return results
