"""Tool for creating and configuring a complete announcement channel setup.

This workflow tool creates an announcement channel and sets up appropriate permissions
to control who can post messages and create threads. It's ideal for setting up
channels where only specific users should be able to post while everyone can read.
"""

from typing import Annotated, Dict, Optional

from arcade.context import ToolContext
from arcade.tool import Discord, tool
from arcade_discord.exceptions import DiscordAPIError, DiscordValidationError
from arcade_discord.utils import (
    CHANNEL_WRITE_SCOPES,
    ROLE_READ_SCOPES,
    check_required_params,
    check_string_length,
    format_channel_for_response,
    make_discord_request,
)


@tool(
    requires_auth=Discord(
        scopes=CHANNEL_WRITE_SCOPES + ROLE_READ_SCOPES,  # More specific scopes
    )
)
async def create_announcement_channel(
    context: ToolContext,
    server_id: Annotated[
        str,
        "The unique ID of the Discord server where you want to create the announcement channel. "
        "This is a numeric string typically 17-20 digits long.",
    ],
    channel_name: Annotated[
        str,
        "Name of the announcement channel (2-100 characters). Use descriptive names "
        "like 'announcements', 'news', or 'important-updates'. Spaces are not allowed; "
        "use hyphens instead.",
    ],
    announcement_description: Annotated[
        str,
        "Description/topic for the announcement channel (0-1024 characters). This helps users "
        "understand the purpose of the channel and appears in the channel info section. "
        "Example: 'Official announcements from the server administrators.'",
    ],
    restrict_posting: Annotated[
        bool,
        "Whether to restrict posting to administrators only. When true, regular members "
        "can only read messages but not post new ones. Set to false if you want everyone "
        "to be able to post in this channel.",
    ] = True,
    allow_thread_creation: Annotated[
        bool,
        "Whether to allow members to create threads from announcements. Threads enable "
        "discussions about specific announcements without cluttering the main channel. "
        "Set to false if you want to prevent thread creation entirely.",
    ] = True,
    category_id: Annotated[
        Optional[str],
        "ID of the category to place the channel under. Categories help organize channels "
        "in the server sidebar. Must be a valid category ID from the same server.",
    ] = None,
) -> Annotated[
    Dict,
    "Details of the created announcement channel setup including permissions and configuration",
]:
    """
    Create a fully configured announcement channel setup.

    This workflow tool creates an announcement channel and configures appropriate permissions.
    When restrict_posting is enabled, only administrators can post, but everyone can read.
    The tool also configures thread permissions based on the allow_thread_creation setting.

    When to use:
    - When setting up a new Discord community that needs official announcement channels
    - When creating channels for important information that should be controlled by staff
    - When you need a channel for broadcasting messages without allowing general discussion
    - When you want organized discussion through threads but controlled main posts
    - When implementing a moderation strategy with designated announcement areas

    Troubleshooting:
    - Error "Missing Permissions": Ensure the bot has "Manage Channels" and "Manage Roles" permissions
    - Error "Invalid Form Body": Check that the channel name follows Discord's format (no spaces)
    - Error "Missing Access": Verify the bot has access to the server and the specified category
    - Error "Unknown Role": The @everyone role could not be found (very unusual, indicates server issue)
    - Error "Rate Limited": Wait a few minutes before trying again if hitting API limits

    Examples:
    - Create a basic announcement channel for staff messages:
      create_announcement_channel(
          server_id="123456789012345678",
          channel_name="announcements",
          announcement_description="Official server announcements from the staff team."
      )

    - Create an announcement channel where users can discuss via threads:
      create_announcement_channel(
          server_id="123456789012345678",
          channel_name="news-and-updates",
          announcement_description="Latest news and updates about our community.",
          restrict_posting=True,
          allow_thread_creation=True
      )

    - Create a broadcast-only channel without thread discussions:
      create_announcement_channel(
          server_id="123456789012345678",
          channel_name="rules",
          announcement_description="Server rules and guidelines. Please read carefully.",
          restrict_posting=True,
          allow_thread_creation=False
      )

    - Create an announcement channel in a specific category:
      create_announcement_channel(
          server_id="123456789012345678",
          channel_name="events",
          announcement_description="Upcoming community events and activities.",
          category_id="987654321098765432"
      )

    Returns a dictionary containing:
    - channel_id: The unique ID of the created channel (string)
    - channel_name: The name of the announcement channel (string)
    - server_id: The server the channel was created in (string)
    - topic: The channel description/topic (string)
    - permissions: Details about the permission configuration (object)
      - everyone_role_id: The ID of the @everyone role (string)
      - everyone_allow: Bitfield of allowed permissions (integer)
      - everyone_deny: Bitfield of denied permissions (integer)
    - everyone_can_read: Whether everyone can read the channel (boolean)
    - admin_only_posting: Whether posting is restricted to administrators (boolean)
    - thread_creation_allowed: Whether members can create threads (boolean)
    - channel_details: Complete channel information as returned by Discord API (object)
    """
    try:
        # Validate required parameters
        check_required_params(
            server_id=server_id,
            channel_name=channel_name,
            announcement_description=announcement_description,
        )

        # Validate string lengths
        check_string_length(channel_name, "channel_name", 2, 100)
        check_string_length(announcement_description, "announcement_description", 0, 1024)

        # Step 1: Create the announcement channel
        channel_payload = {
            "name": channel_name,
            "type": 0,  # Text channel
            "topic": announcement_description,
        }

        if category_id:
            channel_payload["parent_id"] = category_id

        channel_response = make_discord_request(
            context=context,
            method="POST",
            endpoint=f"/guilds/{server_id}/channels",
            json_data=channel_payload,
            context_message="create announcement channel",
        )

        channel_id = channel_response.get("id")

        # Step 2: Get server roles to find @everyone role
        roles_response = make_discord_request(
            context=context,
            method="GET",
            endpoint=f"/guilds/{server_id}/roles",
            context_message="get server roles",
        )

        everyone_role_id = None
        for role in roles_response:
            if role.get("name") == "@everyone":
                everyone_role_id = role.get("id")
                break

        if not everyone_role_id:
            raise DiscordAPIError(
                message="Unable to find @everyone role in the server",
                developer_message="Could not locate @everyone role in server roles list",
            )

        # Step 3: Configure permissions for @everyone role
        permission_overwrites = []

        # Define permission values
        # VIEW_CHANNEL = 1 << 10
        # SEND_MESSAGES = 1 << 11
        # CREATE_PUBLIC_THREADS = 1 << 34
        # CREATE_PRIVATE_THREADS = 1 << 35

        everyone_allow = 1 << 10  # VIEW_CHANNEL
        everyone_deny = 0

        if restrict_posting:
            everyone_deny |= 1 << 11  # SEND_MESSAGES

        if not allow_thread_creation:
            everyone_deny |= (1 << 34) | (
                1 << 35
            )  # CREATE_PUBLIC_THREADS and CREATE_PRIVATE_THREADS

        permission_overwrites.append({
            "id": everyone_role_id,
            "type": 0,  # Role type
            "allow": str(everyone_allow),
            "deny": str(everyone_deny),
        })

        # Step 4: Update channel with permission overwrites
        update_payload = {"permission_overwrites": permission_overwrites}

        updated_channel = make_discord_request(
            context=context,
            method="PATCH",
            endpoint=f"/channels/{channel_id}",
            json_data=update_payload,
            context_message="update channel permissions",
        )

        # Step 5: Return the complete setup details
        channel_details = format_channel_for_response(updated_channel)

        return {
            "channel_id": channel_id,
            "channel_name": channel_name,
            "server_id": server_id,
            "topic": announcement_description,
            "permissions": {
                "everyone_role_id": everyone_role_id,
                "everyone_allow": everyone_allow,
                "everyone_deny": everyone_deny,
            },
            "everyone_can_read": True,
            "admin_only_posting": restrict_posting,
            "thread_creation_allowed": allow_thread_creation,
            "channel_details": channel_details,  # Include the standardized channel details
        }

    except Exception as e:
        if isinstance(e, (DiscordValidationError, DiscordAPIError)):
            raise e
        raise DiscordAPIError(
            message="Failed to create announcement channel setup",
            developer_message=f"Error in workflow: {e!s}",
        )
