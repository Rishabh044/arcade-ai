def parse_guild_list(guilds: list) -> list:
    """Helper function to parse and simplify guild data.
    Args:
        guilds: list of partial guild objects the user is a member of
    Returns:
        list of simplified guild data
    """
    return [
        {
            "id": guild.get("id"),
            "name": guild.get("name"),
            "owner": guild.get("owner"),
            "permissions": guild.get("permissions"),
            "features": guild.get("features"),
            "approximate_member_count": guild.get("approximate_member_count"),
            "approximate_presence_count": guild.get("approximate_presence_count"),
        }
        for guild in guilds
    ]
