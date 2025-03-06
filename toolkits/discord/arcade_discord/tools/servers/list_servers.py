"""Tool for listing Discord servers (guilds) the bot is a member of."""

from typing import Annotated, Dict

from arcade.context import ToolContext
from arcade.tool import Discord, tool
from arcade_discord.utils import SERVER_READ_SCOPES, make_discord_request, parse_server


@tool(
    requires_auth=Discord(
        scopes=SERVER_READ_SCOPES,
    )
)
async def list_servers(
    context: ToolContext,
    limit: Annotated[int, "Maximum number of servers to retrieve"] = 100,
    with_counts: Annotated[bool, "Include approximate member counts"] = True,
) -> Annotated[Dict, "List of Discord servers the bot is a member of"]:
    """
    List Discord servers the bot is a member of.

    This tool retrieves a list of Discord servers (guilds) where the bot has been installed.
    For each server, it provides basic information like name, ID, icon, and optionally
    the approximate member count.

    Examples:
    - Display a list of servers where the bot is installed
    - Get server IDs to use with other Discord tools
    - Show server member counts to monitor bot reach
    - Generate a dashboard of servers the bot is serving

    Returns a dictionary containing:
    - servers: List of server objects with IDs, names, and other details
    - total_count: The total number of servers retrieved
    """
    # Send the request to Discord API
    params = {}
    if with_counts:
        params["with_counts"] = "true"

    if limit > 0:
        params["limit"] = min(limit, 200)  # Discord max limit is 200

    response = make_discord_request(
        context=context,
        method="GET",
        endpoint="/users/@me/guilds",
        params=params,
        context_message="list servers",
    )

    # Parse servers
    servers = []
    for server_data in response:
        server = parse_server(server_data)
        servers.append({
            "id": server.id,
            "name": server.name,
            "icon": server.icon_url,
            "owner": server.owner,
            "permissions": server.permissions,
            "approximate_member_count": server.approximate_member_count,
            "approximate_presence_count": server.approximate_presence_count,
        })

    # Return in a user-friendly format
    return {
        "servers": servers,
        "total_count": len(servers),
    }
