from typing import Annotated

from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import Discord

from arcade_discord.client import DiscordClient


# TODO: Apparantly, there isn't an oauth scope that grants access to listing a guild's channels.
#       The /guilds/{guild.id}/channels endpoint requires a bot token.
@tool(requires_auth=Discord(scopes=["guilds.members.read", "guilds"]))
async def list_channels_in_guild(
    context: ToolContext,
    guild_id: Annotated[str, "The ID of the guild to list channels for"],
) -> dict:
    """Get a list of the channels in a guild (server). Does not include threads."""

    client = DiscordClient(context.get_auth_token_or_empty())
    channels = await client.get_guild_channels(
        guild_id
    )  # will return a 401 because we dont have a bot token

    return {"channels": channels}


# TODO: Apparantly, there isn't an oauth scope that grants access to listing a guild's members.
#       The /guilds/{guild.id}/members endpoint requires a bot token
#       with GUILD_MEMBERS privileged intent
@tool(requires_auth=Discord(scopes=["guilds.members.read", "guilds"]))
async def list_members_in_guild(
    context: ToolContext,
    guild_id: Annotated[str, "The ID of the guild to list members for"],
) -> dict:
    """Get a list of the members in a guild."""

    client = DiscordClient(context.get_auth_token_or_empty())
    members = await client.list_guild_members(guild_id)  # TODO: pagination?

    return {"members": members}
