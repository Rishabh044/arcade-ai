"""Discord message reaction tools.

This module provides tools for adding and managing emoji reactions to Discord messages.
"""

import logging
from typing import Annotated, Dict, Optional

from arcade.core.tool import tool
from arcade.core.tool_context import ToolContext
from arcade.providers.discord import Discord

from ...auth import MESSAGE_SCOPES
from ...client import get_discord_client
from ...exceptions import DiscordPermissionError

logger = logging.getLogger(__name__)


@tool(
    requires_auth=Discord(
        scopes=MESSAGE_SCOPES,
    )
)
async def add_reaction(
    context: ToolContext,
    channel_id: Annotated[str, "ID of the channel containing the message"],
    message_id: Annotated[str, "ID of the message to add reaction to"],
    emoji: Annotated[str, "Emoji to react with (Unicode emoji or custom emoji ID)"],
) -> Annotated[Dict, "Result of adding the reaction"]:
    """
    Add an emoji reaction to a Discord message.

    This tool adds a reaction emoji to a specified message. You can use either standard
    Unicode emojis (like "👍" or "❤️") or custom Discord emojis (using their ID in the
    format "name:id").

    Message reactions are useful for creating polls, allowing quick feedback, building
    role-assignment systems, or simply expressing emotion in response to a message.

    Examples:
    - Add a thumbs up reaction to acknowledge a suggestion
    - React with a check mark to indicate approval of a proposal
    - Create a poll by adding multiple reaction options to a message
    - Add a custom server emoji to welcome new members

    Returns a dictionary containing:
    - channel_id: ID of the channel containing the message
    - message_id: ID of the message that was reacted to
    - emoji: The emoji that was added as a reaction
    - success: Boolean indicating if the reaction was successfully added
    """
    client = await get_discord_client(context)

    try:
        # Format the emoji appropriately for the API
        formatted_emoji = emoji
        if ":" in emoji and not emoji.startswith("<:"):
            # This is likely a custom emoji in name:id format - convert to Discord's format
            name, emoji_id = emoji.split(":")
            formatted_emoji = f"{name}:{emoji_id}"

        # Add the reaction
        await client.create_reaction(
            channel_id=channel_id, message_id=message_id, emoji=formatted_emoji
        )

        # Format response
        return {
            "channel_id": channel_id,
            "message_id": message_id,
            "emoji": emoji,
            "success": True,
        }

    except Exception as e:
        logger.error(f"Failed to add reaction: {e!s}")
        raise DiscordPermissionError(
            message=f"Could not add reaction to message {message_id}",
            developer_message=f"Failed to add reaction: {e!s}",
        )


@tool(
    requires_auth=Discord(
        scopes=MESSAGE_SCOPES,
    )
)
async def remove_reaction(
    context: ToolContext,
    channel_id: Annotated[str, "ID of the channel containing the message"],
    message_id: Annotated[str, "ID of the message to remove reaction from"],
    emoji: Annotated[str, "Emoji to remove (Unicode emoji or custom emoji ID)"],
    user_id: Annotated[
        Optional[str],
        "ID of the user whose reaction to remove (if not specified, removes bot's reaction)",
    ] = None,
) -> Annotated[Dict, "Result of removing the reaction"]:
    """
    Remove an emoji reaction from a Discord message.

    This tool removes a reaction emoji from a specified message. You can remove either
    your bot's own reaction or a specific user's reaction (if you have the MANAGE_MESSAGES
    permission).

    Removing reactions is useful for cleaning up polls after they're completed, managing
    reaction-based role systems, or controlling the available options in a menu.

    Examples:
    - Remove your bot's checkmark reaction after a request is processed
    - Clean up a user's reaction in a controlled reaction-role system
    - Remove all instances of a specific reaction from a poll that has ended
    - Take away inappropriate reactions added by users

    Returns a dictionary containing:
    - channel_id: ID of the channel containing the message
    - message_id: ID of the message that had the reaction removed
    - emoji: The emoji that was removed as a reaction
    - user_id: ID of the user whose reaction was removed (if specified)
    - success: Boolean indicating if the reaction was successfully removed
    """
    client = await get_discord_client(context)

    try:
        # Format the emoji appropriately for the API
        formatted_emoji = emoji
        if ":" in emoji and not emoji.startswith("<:"):
            # This is likely a custom emoji in name:id format - convert to Discord's format
            name, emoji_id = emoji.split(":")
            formatted_emoji = f"{name}:{emoji_id}"

        if user_id:
            # Remove a specific user's reaction
            await client.delete_user_reaction(
                channel_id=channel_id, message_id=message_id, emoji=formatted_emoji, user_id=user_id
            )
        else:
            # Remove the bot's own reaction
            await client.delete_own_reaction(
                channel_id=channel_id, message_id=message_id, emoji=formatted_emoji
            )

        # Format response
        return {
            "channel_id": channel_id,
            "message_id": message_id,
            "emoji": emoji,
            "user_id": user_id,
            "success": True,
        }

    except Exception as e:
        logger.error(f"Failed to remove reaction: {e!s}")
        raise DiscordPermissionError(
            message=f"Could not remove reaction from message {message_id}",
            developer_message=f"Failed to remove reaction: {e!s}",
        )


@tool(
    requires_auth=Discord(
        scopes=MESSAGE_SCOPES,
    )
)
async def get_reactions(
    context: ToolContext,
    channel_id: Annotated[str, "ID of the channel containing the message"],
    message_id: Annotated[str, "ID of the message to get reactions from"],
    emoji: Annotated[
        Optional[str], "Specific emoji to get reactions for (if not specified, returns all)"
    ] = None,
) -> Annotated[Dict, "Reactions on the message"]:
    """
    Get the list of users who reacted to a Discord message.

    This tool retrieves all users who have added a specific reaction to a message. If no
    emoji is specified, it will return information about all reactions on the message.

    Getting reaction data is useful for tallying poll results, determining who participated
    in a reaction-based system, or analyzing engagement with a message.

    Examples:
    - Count votes in a reaction-based poll
    - Check which users have signed up via a reaction
    - Determine the most popular reaction to a message
    - Verify if a specific user has reacted to a message

    Returns a dictionary containing:
    - channel_id: ID of the channel containing the message
    - message_id: ID of the message that was queried
    - reactions: List of reaction objects with emoji and user details
    - count: Total count of reactions found
    """
    client = await get_discord_client(context)

    try:
        if emoji:
            # Format the emoji appropriately for the API
            formatted_emoji = emoji
            if ":" in emoji and not emoji.startswith("<:"):
                # This is likely a custom emoji in name:id format - convert to Discord's format
                name, emoji_id = emoji.split(":")
                formatted_emoji = f"{name}:{emoji_id}"

            # Get users who reacted with a specific emoji
            users = await client.get_reactions(
                channel_id=channel_id, message_id=message_id, emoji=formatted_emoji
            )

            reaction_data = [
                {
                    "emoji": emoji,
                    "users": [
                        {"id": user.get("id"), "username": user.get("username")} for user in users
                    ],
                    "count": len(users),
                }
            ]
        else:
            # Get the message to see all reactions
            message = await client.get_channel_message(channel_id=channel_id, message_id=message_id)

            # Extract reaction data
            reaction_data = []
            if "reactions" in message:
                for reaction in message.get("reactions", []):
                    reaction_data.append({
                        "emoji": {
                            "name": reaction.get("emoji", {}).get("name"),
                            "id": reaction.get("emoji", {}).get("id"),
                        },
                        "count": reaction.get("count", 0),
                        # We don't have user details without making additional API calls for each emoji
                    })

        # Format response
        return {
            "channel_id": channel_id,
            "message_id": message_id,
            "reactions": reaction_data,
            "count": sum(r.get("count", 0) for r in reaction_data),
        }

    except Exception as e:
        logger.error(f"Failed to get reactions: {e!s}")
        raise DiscordPermissionError(
            message=f"Could not get reactions from message {message_id}",
            developer_message=f"Failed to get reactions: {e!s}",
        )
