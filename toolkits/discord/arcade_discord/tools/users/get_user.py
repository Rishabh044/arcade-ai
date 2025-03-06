"""Discord user information tools.

This module provides tools for retrieving information about Discord users.
"""

import logging
from typing import Annotated, Dict, Optional

from arcade.core.tool import tool
from arcade.core.tool_context import ToolContext
from arcade.providers.discord import Discord

from ...auth import SERVER_SCOPES, USER_SCOPES
from ...client import get_discord_client
from ...exceptions import DiscordPermissionError

logger = logging.getLogger(__name__)


@tool(
    requires_auth=Discord(
        scopes=USER_SCOPES,
    )
)
async def get_user(
    context: ToolContext,
    user_id: Annotated[str, "ID of the user to retrieve information about"],
) -> Annotated[Dict, "User information"]:
    """
    Get information about a Discord user.

    This tool retrieves basic profile information about any Discord user by their ID.
    The information includes their username, avatar, account creation date, and other
    public profile details.

    This is useful for verifying user identities, gathering profile information, or
    checking if a user exists on Discord.

    Examples:
    - Verify the identity of a user requesting access to a channel
    - Check when a user's account was created for moderation purposes
    - Get a user's avatar URL to display in an embed
    - Confirm a user exists before attempting to add them to a channel

    Returns a dictionary containing:
    - id: The user's unique Discord ID
    - username: The user's current display name
    - discriminator: The user's discriminator (if using the legacy username system)
    - avatar: URL to the user's avatar image
    - bot: Boolean indicating if the account is a bot
    - system: Boolean indicating if the account is an official Discord system user
    - banner: URL to the user's profile banner (if they have one)
    - created_at: Timestamp of when the account was created
    """
    client = await get_discord_client(context)

    try:
        # Get the user data
        user_data = await client.get_user(user_id)

        # Calculate account creation time from the ID
        # Discord IDs contain creation timestamp in bits 22-63
        created_timestamp = ((int(user_id) >> 22) + 1420070400000) / 1000

        # Format avatar URL if available
        avatar_hash = user_data.get("avatar")
        avatar_url = None
        if avatar_hash:
            avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png"

        # Format banner URL if available
        banner_hash = user_data.get("banner")
        banner_url = None
        if banner_hash:
            banner_url = f"https://cdn.discordapp.com/banners/{user_id}/{banner_hash}.png"

        # Format response
        return {
            "id": user_data.get("id"),
            "username": user_data.get("username"),
            "discriminator": user_data.get("discriminator"),
            "avatar": avatar_url,
            "bot": user_data.get("bot", False),
            "system": user_data.get("system", False),
            "banner": banner_url,
            "created_at": created_timestamp,
        }

    except Exception as e:
        logger.error(f"Failed to get user: {e!s}")
        raise DiscordPermissionError(
            message=f"Could not retrieve information for user {user_id}",
            developer_message=f"Failed to get user: {e!s}",
        )


@tool(
    requires_auth=Discord(
        scopes=SERVER_SCOPES,
    )
)
async def get_server_member(
    context: ToolContext,
    server_id: Annotated[str, "ID of the server the user is in"],
    user_id: Annotated[str, "ID of the user to retrieve information about"],
) -> Annotated[Dict, "Server member information"]:
    """
    Get information about a user's membership in a specific Discord server.

    This tool retrieves detailed information about a user's presence in a server,
    including their nickname, roles, join date, and server-specific profile settings.
    This provides more context than the basic user information from get_user().

    This is useful for moderation tasks, checking a user's server history, determining
    their permissions, or personalizing interactions based on their server profile.

    Examples:
    - Check if a user has a custom nickname in your server
    - Determine when a user joined your server for anniversary celebrations
    - Get a complete list of roles assigned to a user
    - Verify if a user has been server boosting and for how long

    Returns a dictionary containing:
    - user: Basic user information (id, username, avatar)
    - nick: The user's server-specific nickname (if set)
    - roles: List of role IDs assigned to the user
    - joined_at: Timestamp of when the user joined the server
    - premium_since: Timestamp of when the user started boosting the server (if applicable)
    - pending: Whether the user has completed server membership screening
    - communication_disabled_until: Timeout expiration time (if user is timed out)
    """
    client = await get_discord_client(context)

    try:
        # Get the member data
        member_data = await client.get_guild_member(guild_id=server_id, user_id=user_id)

        # Extract user info
        user_info = member_data.get("user", {})

        # Format avatar URL if available
        avatar_hash = user_info.get("avatar")
        avatar_url = None
        if avatar_hash:
            avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png"

        # Format response
        return {
            "user": {
                "id": user_info.get("id"),
                "username": user_info.get("username"),
                "discriminator": user_info.get("discriminator"),
                "avatar": avatar_url,
                "bot": user_info.get("bot", False),
            },
            "nick": member_data.get("nick"),
            "roles": member_data.get("roles", []),
            "joined_at": member_data.get("joined_at"),
            "premium_since": member_data.get("premium_since"),
            "pending": member_data.get("pending", False),
            "communication_disabled_until": member_data.get("communication_disabled_until"),
        }

    except Exception as e:
        logger.error(f"Failed to get server member: {e!s}")
        raise DiscordPermissionError(
            message=f"Could not retrieve information for user {user_id} in server {server_id}",
            developer_message=f"Failed to get server member: {e!s}",
        )


@tool(
    requires_auth=Discord(
        scopes=SERVER_SCOPES,
    )
)
async def list_server_members(
    context: ToolContext,
    server_id: Annotated[str, "ID of the server to list members from"],
    limit: Annotated[Optional[int], "Maximum number of members to retrieve (1-1000)"] = 100,
    after: Annotated[Optional[str], "Get members after this user ID (for pagination)"] = None,
) -> Annotated[Dict, "List of server members"]:
    """
    Get a list of members in a Discord server.

    This tool retrieves information about members in a specified server, with options to
    limit the number of results and implement pagination. The list includes basic user
    information and server-specific details like nicknames and roles.

    This is useful for creating member directories, performing server analytics, finding
    specific types of members, or implementing server-wide operations.

    Examples:
    - Create a member directory for a community server
    - Generate statistics about server demographics or roles
    - Implement a member search feature within your bot
    - Get a list of all users with a specific role for targeted announcements

    Returns a dictionary containing:
    - server_id: ID of the server whose members were listed
    - members: List of member objects with user details and server-specific information
    - count: Number of members returned in this response
    - has_more: Boolean indicating if there are more members that can be retrieved
    """
    client = await get_discord_client(context)

    # Validate input parameters
    if limit is not None:
        limit = max(1, min(limit, 1000))  # Ensure limit is between 1 and 1000

    try:
        # Get the member data
        members = await client.list_guild_members(guild_id=server_id, limit=limit, after=after)

        # Format response
        formatted_members = []
        for member in members:
            user_info = member.get("user", {})
            user_id = user_info.get("id")

            # Format avatar URL if available
            avatar_hash = user_info.get("avatar")
            avatar_url = None
            if avatar_hash:
                avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png"

            formatted_members.append({
                "user": {
                    "id": user_id,
                    "username": user_info.get("username"),
                    "discriminator": user_info.get("discriminator"),
                    "avatar": avatar_url,
                    "bot": user_info.get("bot", False),
                },
                "nick": member.get("nick"),
                "roles": member.get("roles", []),
                "joined_at": member.get("joined_at"),
                "premium_since": member.get("premium_since"),
            })

        # Determine if there are more members to fetch
        has_more = len(members) == limit

        return {
            "server_id": server_id,
            "members": formatted_members,
            "count": len(formatted_members),
            "has_more": has_more,
        }

    except Exception as e:
        logger.error(f"Failed to list server members: {e!s}")
        raise DiscordPermissionError(
            message=f"Could not retrieve members for server {server_id}",
            developer_message=f"Failed to list server members: {e!s}",
        )
