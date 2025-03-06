"""Tool for retrieving information about a Discord server (guild)."""

from typing import Annotated, Dict

from arcade.context import ToolContext
from arcade.tool import Discord, tool
from arcade_discord.exceptions import DiscordValidationError
from arcade_discord.utils import SERVER_SCOPES, make_discord_request, parse_server


@tool(
    requires_auth=Discord(
        scopes=SERVER_SCOPES,
    )
)
async def get_server(
    context: ToolContext,
    server_id: Annotated[str, "ID of the server (guild) to retrieve"],
    with_counts: Annotated[bool, "Include approximate member counts"] = True,
) -> Annotated[Dict, "Details of the Discord server"]:
    """
    Get information about a Discord server (guild).

    This tool retrieves detailed information about a specific Discord server,
    including its name, description, icon, and optionally member counts.
    The bot must be a member of the server to retrieve this information.

    Example:
        ```python
        get_server(server_id="123456789012345678", with_counts=True)
        ```
    """
    # Validation
    if not server_id:
        raise DiscordValidationError(
            message="Server ID is required",
            developer_message="server_id parameter was empty or None",
        )

    # Prepare query parameters
    params = {}
    if with_counts:
        params["with_counts"] = "true"

    # Send the request to Discord API
    response = make_discord_request(
        context=context,
        method="GET",
        endpoint=f"/guilds/{server_id}",
        params=params,
        context_message="get server information",
    )

    # Parse server data
    server = parse_server(response)

    # Return in a user-friendly format
    result = {
        "id": server.id,
        "name": server.name,
        "description": server.description,
        "owner_id": server.owner_id,
        "icon": server.icon,
    }

    if with_counts and server.member_count is not None:
        result["member_count"] = server.member_count

    # Add additional information from the raw response
    if "features" in response:
        result["features"] = response["features"]

    if "preferred_locale" in response:
        result["preferred_locale"] = response["preferred_locale"]

    if "verification_level" in response:
        result["verification_level"] = response["verification_level"]

    return result
