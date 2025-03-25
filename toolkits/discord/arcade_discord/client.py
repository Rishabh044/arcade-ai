from typing import Optional

import httpx


class DiscordClient:
    BASE_URL = "https://discord.com/api/v10"

    def __init__(self, token: str):
        self.token = token

    async def request(self, method: str, endpoint: str, **kwargs) -> dict:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method, f"{self.BASE_URL}/{endpoint}", headers=headers, **kwargs
            )
            response.raise_for_status()
            return response.json()

    # User endpoints

    async def get_current_user_guilds(self, params: Optional[dict] = None) -> dict:
        """Get the guilds the user is a member of

        Implements https://discord.com/developers/docs/resources/user#get-current-user-guilds
        """
        return await self.request("GET", "users/@me/guilds", params=params)

    async def get_current_user_guild_member(self, guild_id: str) -> dict:
        """Get the guild member object for the current user

        Implements https://discord.com/developers/docs/resources/user#get-current-user-guild-member
        """
        return await self.request("GET", f"users/@me/guilds/{guild_id}/member")

    # Guild endpoints

    async def get_guild_channels(self, guild_id: str) -> dict:
        """Get the channels in a guild

        Implements https://discord.com/developers/docs/resources/guild#get-guild-channels
        """
        return await self.request("GET", f"guilds/{guild_id}/channels")

    async def list_guild_members(self, guild_id: str) -> dict:
        """Get the members in a guild

        Implements https://discord.com/developers/docs/resources/guild#list-guild-members
        """
        return await self.request("GET", f"guilds/{guild_id}/members")
