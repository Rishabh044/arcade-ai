"""Discord role management tools.

This module provides tools for creating, updating, and managing roles in Discord servers.
"""

import logging
from typing import Annotated, Dict, List, Optional

from arcade.core.tool import tool
from arcade.core.tool_context import ToolContext
from arcade.providers.discord import Discord

from ...auth import ROLE_SCOPES, SERVER_SCOPES
from ...client import get_discord_client
from ...exceptions import DiscordPermissionError, DiscordValidationError

logger = logging.getLogger(__name__)


@tool(
    requires_auth=Discord(
        scopes=ROLE_SCOPES,
    )
)
async def create_role(
    context: ToolContext,
    server_id: Annotated[str, "ID of the server to create the role in"],
    name: Annotated[str, "Name for the new role"],
    color: Annotated[Optional[int], "RGB color for the role (as integer)"] = None,
    hoist: Annotated[
        bool, "Whether the role should be displayed separately in member list"
    ] = False,
    mentionable: Annotated[bool, "Whether the role can be mentioned by anyone"] = False,
    permissions: Annotated[Optional[List[str]], "List of permission names to grant"] = None,
    reason: Annotated[Optional[str], "Reason for creating this role (for audit logs)"] = None,
) -> Annotated[Dict, "Details of the created role"]:
    """
    Create a new role in a Discord server.

    This tool allows you to create customized roles with specific colors, visibility
    settings, and permissions. Roles can be used to organize members, manage permissions,
    and create hierarchies within a Discord server.

    When specifying permissions, use standard Discord permission names like "KICK_MEMBERS",
    "BAN_MEMBERS", "ADMINISTRATOR", etc. Invalid permission names will be ignored.

    Examples:
    - Create a moderator role with permissions to manage messages and kick members
    - Set up a colorful role for a special event or team
    - Create a mentionable role to notify everyone with that role
    - Make a role that's displayed separately in the member list for visibility

    Returns a dictionary containing:
    - id: Unique identifier for the created role
    - name: Name of the role
    - color: Hex color code of the role
    - position: Position in the role hierarchy
    - permissions: Integer representing the role's permissions
    - mentionable: Whether the role can be mentioned
    - hoist: Whether the role is displayed separately
    """
    client = await get_discord_client(context)

    # Validate input parameters
    if not name or len(name) > 100:
        raise DiscordValidationError(
            message="Role name must be between 1 and 100 characters",
            developer_message="Invalid role name length",
        )

    # Convert permission names to the permissions integer if provided
    permission_int = 0
    if permissions:
        # This would convert permission names to the correct bit flags
        # For simplicity, we'll just set some basic values here
        permission_map = {
            "ADMINISTRATOR": 1 << 3,
            "KICK_MEMBERS": 1 << 1,
            "BAN_MEMBERS": 1 << 2,
            "MANAGE_CHANNELS": 1 << 4,
            "MANAGE_GUILD": 1 << 5,
            "MANAGE_MESSAGES": 1 << 13,
            "MENTION_EVERYONE": 1 << 17,
            "MUTE_MEMBERS": 1 << 22,
            "DEAFEN_MEMBERS": 1 << 23,
            "MOVE_MEMBERS": 1 << 24,
            "MANAGE_NICKNAMES": 1 << 27,
            "MANAGE_ROLES": 1 << 28,
            "MANAGE_WEBHOOKS": 1 << 29,
            "MANAGE_EMOJIS": 1 << 30,
        }

        for perm in permissions:
            if perm in permission_map:
                permission_int |= permission_map[perm]

    try:
        # Create the role
        payload = {
            "name": name,
            "permissions": permission_int,
            "hoist": hoist,
            "mentionable": mentionable,
        }

        if color is not None:
            payload["color"] = color

        if reason:
            payload["reason"] = reason

        role = await client.create_guild_role(guild_id=server_id, **payload)

        # Format response
        return {
            "id": role.get("id"),
            "name": role.get("name"),
            "color": role.get("color"),
            "position": role.get("position"),
            "permissions": role.get("permissions"),
            "mentionable": role.get("mentionable"),
            "hoist": role.get("hoist"),
            "created_success": True,
        }

    except Exception as e:
        logger.error(f"Failed to create role: {e!s}")
        raise DiscordPermissionError(
            message=f"Could not create role in server {server_id}",
            developer_message=f"Failed to create role: {e!s}",
        )


@tool(
    requires_auth=Discord(
        scopes=ROLE_SCOPES,
    )
)
async def assign_role(
    context: ToolContext,
    server_id: Annotated[str, "ID of the server containing the role"],
    user_id: Annotated[str, "ID of the user to assign the role to"],
    role_id: Annotated[str, "ID of the role to assign"],
    reason: Annotated[Optional[str], "Reason for assigning this role (for audit logs)"] = None,
) -> Annotated[Dict, "Result of the role assignment"]:
    """
    Assign a role to a user in a Discord server.

    This tool adds a specified role to a user, which grants them all permissions and
    visibility settings associated with that role. Role assignments are useful for
    granting permissions, identifying user groups, and controlling access to channels.

    The bot must have MANAGE_ROLES permission and a role higher than the one being
    assigned in the role hierarchy.

    Examples:
    - Assign a moderator role to a trusted community member
    - Add a member to a team role to grant access to team channels
    - Give a special event role to participants
    - Assign a verification role to users who completed onboarding

    Returns a dictionary containing:
    - server_id: ID of the server where the role was assigned
    - user_id: ID of the user who received the role
    - role_id: ID of the role that was assigned
    - success: Boolean indicating if the assignment was successful
    """
    client = await get_discord_client(context)

    try:
        # Add the role to the member
        await client.add_guild_member_role(
            guild_id=server_id,
            user_id=user_id,
            role_id=role_id,
            reason=reason or "Role assigned via Arcade Discord toolkit",
        )

        # Format response
        return {
            "server_id": server_id,
            "user_id": user_id,
            "role_id": role_id,
            "success": True,
            "action": "assigned",
        }

    except Exception as e:
        logger.error(f"Failed to assign role: {e!s}")
        raise DiscordPermissionError(
            message=f"Could not assign role {role_id} to user {user_id}",
            developer_message=f"Failed to assign role: {e!s}",
        )


@tool(
    requires_auth=Discord(
        scopes=ROLE_SCOPES,
    )
)
async def remove_role(
    context: ToolContext,
    server_id: Annotated[str, "ID of the server containing the role"],
    user_id: Annotated[str, "ID of the user to remove the role from"],
    role_id: Annotated[str, "ID of the role to remove"],
    reason: Annotated[Optional[str], "Reason for removing this role (for audit logs)"] = None,
) -> Annotated[Dict, "Result of the role removal"]:
    """
    Remove a role from a user in a Discord server.

    This tool removes a specified role from a user, revoking any permissions or settings
    granted by that role. Role removal is useful for demotions, ending temporary access,
    or removing users from groups or teams.

    The bot must have MANAGE_ROLES permission and a role higher than the one being
    removed in the role hierarchy.

    Examples:
    - Remove a temporary event role after the event concludes
    - Revoke moderator permissions from a stepping-down moderator
    - Remove a team role when someone leaves a project
    - Take away a special access role when no longer needed

    Returns a dictionary containing:
    - server_id: ID of the server where the role was removed
    - user_id: ID of the user who lost the role
    - role_id: ID of the role that was removed
    - success: Boolean indicating if the removal was successful
    """
    client = await get_discord_client(context)

    try:
        # Remove the role from the member
        await client.remove_guild_member_role(
            guild_id=server_id,
            user_id=user_id,
            role_id=role_id,
            reason=reason or "Role removed via Arcade Discord toolkit",
        )

        # Format response
        return {
            "server_id": server_id,
            "user_id": user_id,
            "role_id": role_id,
            "success": True,
            "action": "removed",
        }

    except Exception as e:
        logger.error(f"Failed to remove role: {e!s}")
        raise DiscordPermissionError(
            message=f"Could not remove role {role_id} from user {user_id}",
            developer_message=f"Failed to remove role: {e!s}",
        )


@tool(
    requires_auth=Discord(
        scopes=SERVER_SCOPES,
    )
)
async def list_roles(
    context: ToolContext,
    server_id: Annotated[str, "ID of the server to list roles from"],
) -> Annotated[Dict, "List of roles in the server"]:
    """
    List all roles in a Discord server.

    This tool retrieves all roles from a server, including their IDs, names, colors,
    and permission settings. Listing roles is useful for getting role IDs, checking
    the role hierarchy, or auditing server permissions.

    The list is returned in the server's role hierarchy order, with higher positions
    having more authority.

    Examples:
    - Get a list of all roles to reference their IDs in other commands
    - Check which roles are hoisted (shown separately) in the member list
    - Audit which roles have sensitive permissions like administrator
    - View the complete role hierarchy to understand server structure

    Returns a dictionary containing:
    - server_id: ID of the server whose roles were listed
    - roles: List of role objects with their properties
    - count: Total number of roles in the server
    """
    client = await get_discord_client(context)

    try:
        # Get all roles from the server
        roles = await client.get_guild_roles(server_id)

        # Format response
        formatted_roles = []
        for role in roles:
            formatted_roles.append({
                "id": role.get("id"),
                "name": role.get("name"),
                "color": role.get("color"),
                "position": role.get("position"),
                "permissions": role.get("permissions"),
                "mentionable": role.get("mentionable"),
                "hoist": role.get("hoist"),
                "managed": role.get("managed"),
            })

        # Sort by position (higher positions have more authority)
        formatted_roles.sort(key=lambda r: r["position"], reverse=True)

        return {
            "server_id": server_id,
            "roles": formatted_roles,
            "count": len(formatted_roles),
        }

    except Exception as e:
        logger.error(f"Failed to list roles: {e!s}")
        raise DiscordPermissionError(
            message=f"Could not list roles for server {server_id}",
            developer_message=f"Failed to list roles: {e!s}",
        )
