# Discord API Documentation for Arcade Toolkit

## Overview

This toolkit provides a streamlined interface to Discord's API, handling authentication, validation, and error management for server, channel, message, and webhook operations.

## Authentication

Discord uses OAuth2 with different scopes:

| Scope | Used For |
| --- | --- |
| `bot` | Most operations |
| `applications.commands` | Slash commands |
| `messages.read` | Reading messages |
| `messages.write` | Sending/editing messages |
| `channels.read` | Viewing channels |
| `channels.write` | Creating/updating channels |
| `guilds.read` | Server information |
| `guilds.members.read` | Member information |
| `guilds.roles.write` | Role management |
| `webhook.incoming` | Webhook operations |

## Core Features

### Messages
- Send, list, edit, and delete messages
- Add/remove emoji reactions

### Channels
- List, create, update, and delete channels

### Servers (Guilds)
- List servers and view server details
- Manage server members

### Webhooks
- Create and execute webhooks

### Roles & Threads
- Create and manage roles and thread conversations

### Gateway
- Listen for real-time Discord events

## Data Validation

The toolkit validates all Discord-specific data types:

```python
# Validate Discord IDs (snowflakes)
channel_id = validate_discord_id("123456789012345678", "channel_id")

# Normalize channel names
channel_name = validate_channel_name("My Channel")  # Returns "my-channel"

# Validate message content
validate_message_content(content="Hello", embed={"title": "Title"})

# Validate embeds and colors
validate_embed({"title": "Announcement", "description": "Update"})
validate_color(0x3498db)  # Blue
```

## Common Patterns

### Sending Messages with Embeds

```python
from arcade_discord import send_message, Embed, EmbedField

embed = Embed(
    title="Important Message",
    description="This is an important update",
    color=0x3498db,  # Blue
    fields=[
        EmbedField(name="Status", value="Online", inline=True),
        EmbedField(name="Uptime", value="99.9%", inline=True)
    ]
)

send_message(
    channel_id="123456789012345678",
    content="Please read this update:",
    embed=embed
)
```

### Combined Operations

```python
# Create channel and post message
result = create_and_post(
    server_id="123456789012345678",
    channel_name="announcements",
    message_content="First announcement!",
    is_announcement=True
)

# Send formatted message with fields
send_formatted_message(
    channel_id="123456789012345678",
    title="Weekly Report",
    description="Here's what happened",
    fields={
        "New Features": "- Feature A\n- Feature B",
        "Bug Fixes": "- Issue 1 fixed\n- Issue 2 fixed"
    }
)
```

### Working with Webhooks

```python
webhook = create_webhook(
    channel_id="123456789012345678",
    name="Alerts"
)

send_webhook_message(
    webhook_url=webhook["url"],
    content="New deployment completed!",
    username="Deployment Bot",
    avatar_url="https://example.com/avatar.png"
)
```

## Error Handling

The toolkit provides specific exception types:

| Exception | Description |
| --- | --- |
| `DiscordAuthError` | Authentication failures |
| `DiscordPermissionError` | Missing permissions |
| `DiscordRateLimitError` | Rate limits exceeded |
| `DiscordValidationError` | Invalid parameters |
| `DiscordResourceNotFoundError` | Resource not found |
| `DiscordWebhookError` | Webhook-specific errors |

Example:

```python
try:
    send_message(channel_id="123456789012345678", content="Hello!")
except DiscordValidationError as e:
    print(f"Validation error: {e.message}")
except DiscordRateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except DiscordResourceNotFoundError:
    print("Channel not found")
```

## Best Practices

1. **Use Least Privilege**: Request only needed scopes
2. **Handle Rate Limits**: Add proper error handling
3. **Validate Inputs**: Use provided validation utilities
4. **Use Strong Types**: Leverage type safety with model classes
5. **Store IDs as Strings**: Discord IDs are snowflakes (strings)
6. **Check Permissions**: Ensure the bot has necessary permissions
7. **Use Helper Tools**: Leverage example tools for common operations

## Resources

- [Discord Developer Portal](https://discord.com/developers/applications)
- [Discord API Documentation](https://discord.com/developers/docs)
