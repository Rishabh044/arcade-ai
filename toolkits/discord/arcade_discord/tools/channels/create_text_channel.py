"""Tool for creating a new text channel in a Discord server.

This tool allows you to create a standard text channel in a Discord server with
customizable settings including topic, category placement, slowmode rate limiting,
and NSFW flagging.
"""

from typing import Annotated, Dict, Optional

from arcade.context import ToolContext
from arcade.tool import Discord, tool
from arcade_discord.utils import (
    CHANNEL_WRITE_SCOPES,
    check_numeric_range,
    check_required_params,
    check_string_length,
    format_channel_for_response,
    make_discord_request,
)


@tool(
    requires_auth=Discord(
        scopes=CHANNEL_WRITE_SCOPES,  # More specific scope - only need channel write
    )
)
async def create_text_channel(
    context: ToolContext,
    server_id: Annotated[
        str,
        "The unique ID of the Discord server where you want to create the channel. "
        "This is a numeric string typically 17-20 digits long.",
    ],
    name: Annotated[
        str,
        "Name of the channel (2-100 characters). Must not contain spaces; use hyphens instead. "
        "Examples: 'general', 'support-chat', 'announcements'.",
    ],
    topic: Annotated[
        Optional[str],
        "Description for the channel that appears in the channel info (0-1024 characters). "
        "This helps users understand the channel's purpose.",
    ] = None,
    parent_category_id: Annotated[
        Optional[str],
        "ID of the category to place the channel under. Categories help organize channels "
        "in the server sidebar. Must be a valid category ID from the same server.",
    ] = None,
    slowmode_timeout: Annotated[
        Optional[int],
        "Slowmode rate limit in seconds (0-21600). Controls how frequently users can post messages. "
        "Higher values (e.g., 5-60) are useful for moderating busy channels.",
    ] = None,
    nsfw: Annotated[
        bool,
        "Whether the channel should be marked as Not Safe For Work. NSFW channels "
        "require age verification and are filtered from search results.",
    ] = False,
) -> Annotated[Dict, "Details of the created channel including ID, name, type, and configuration"]:
    """
    Create a new text channel in a Discord server.

    This tool creates a standard text channel with customizable settings like topic,
    category placement, slowmode, and NSFW flag. The bot must have the Manage Channels
    permission in the server.

    When to use:
    - When setting up a new Discord server and need to create the basic channel structure
    - When expanding an existing server with new channels for specific topics
    - When organizing server content by creating dedicated channels for different discussions
    - When implementing a moderation strategy that requires specialized channels

    Troubleshooting:
    - Error "Missing Permissions": Ensure the bot has the "Manage Channels" permission
    - Error "Invalid Form Body": Check that the channel name follows Discord's format (no spaces)
    - Error "Missing Access": Verify the bot has access to the server and the specified category
    - Error "Rate Limited": Wait a few minutes before trying again if hitting API limits
    - Error "Channel Name Already Used": Choose a different name not already in use in the server

    Examples:
    - Create a basic general chat channel:
      create_text_channel(server_id="123456789012345678", name="general")

    - Create a support channel with a descriptive topic:
      create_text_channel(
          server_id="123456789012345678",
          name="support-tickets",
          topic="Get help with your issues. Please provide detailed information."
      )

    - Create a moderated channel with slowmode:
      create_text_channel(
          server_id="123456789012345678",
          name="community-feedback",
          topic="Share your thoughts about our community",
          slowmode_timeout=30
      )

    - Create an age-restricted channel under a specific category:
      create_text_channel(
          server_id="123456789012345678",
          name="adult-content",
          topic="Content only suitable for adults",
          parent_category_id="987654321098765432",
          nsfw=True
      )

    Returns a dictionary containing:
    - id: The unique ID of the created channel
    - name: The name of the channel
    - type: The channel type (always "text" for this tool)
    - server_id: The server the channel was created in
    - topic: The channel topic (if provided)
    - category_id: The parent category ID (if provided)
    - position: The position of the channel in the channel list
    - nsfw: Whether the channel is marked as NSFW
    - rate_limit_per_user: The slowmode timeout in seconds
    """
    # Validate required parameters
    check_required_params(server_id=server_id, name=name)

    # Validate string parameters
    check_string_length(name, "name", 2, 100)
    if topic:
        check_string_length(topic, "topic", 0, 1024)

    # Validate numeric parameters
    if slowmode_timeout is not None:
        check_numeric_range(slowmode_timeout, "slowmode_timeout", 0, 21600)

    # Prepare the request payload
    payload = {
        "name": name,
        "type": 0,  # 0 is the type for text channels
        "nsfw": nsfw,
    }

    if topic:
        payload["topic"] = topic

    if parent_category_id:
        payload["parent_id"] = parent_category_id

    if slowmode_timeout is not None:
        payload["rate_limit_per_user"] = slowmode_timeout

    # Send the request to Discord API
    response = make_discord_request(
        context=context,
        method="POST",
        endpoint=f"/guilds/{server_id}/channels",
        json_data=payload,
        context_message="create text channel",
    )

    # Return in a user-friendly standardized format
    return format_channel_for_response(response)
