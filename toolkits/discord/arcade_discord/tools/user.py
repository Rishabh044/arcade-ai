from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import Discord

from arcade_discord.client import DiscordClient
from arcade_discord.utils import parse_guild_list


@tool(requires_auth=Discord(scopes=["guilds"]))
async def list_guilds(context: ToolContext) -> dict:
    """Get a list of the guilds (servers) the user is a member of"""

    client = DiscordClient(context.get_auth_token_or_empty())
    params = {"with_counts": True}
    guilds = await client.get_current_user_guilds(params=params)

    guild_list = parse_guild_list(guilds)

    return {"guilds": guild_list}
