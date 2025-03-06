# Discord Toolkit for Arcade AI

Discord integration for Arcade AI that enables interaction with Discord servers, channels, messages, and webhooks.

## Features

- **Messages**: Send, read, edit, and delete messages
- **Channels**: Create, list, and manage channels 
- **Servers**: Get information about Discord servers
- **Users**: Access user information and server members
- **Webhooks**: Create and execute Discord webhooks
- **Reactions**: Manage emoji reactions on messages
- **Roles**: Create, assign, and manage server roles
- **Threads**: Create and manage conversation threads
- **Voice**: Manage voice channels and interactions
- **Gateway**: Listen for real-time events
- **Examples**: Convenient combined operations for common tasks
- **Validation**: Robust input validation with helpful error messages

## Quick Start

```python
from arcade_discord import send_message, create_webhook, send_webhook_message

# Send a message to a channel
response = send_message(
    channel_id="123456789012345678",
    content="Hello from Arcade AI!"
)

# Create and use a webhook
webhook = create_webhook(channel_id="123456789012345678", name="Alerts")
send_webhook_message(webhook_url=webhook["url"], content="Notification!")
```

## Authentication

All tools use minimal OAuth2 scopes following the principle of least privilege:

- **Read operations**: Use read-only scopes
- **Write operations**: Use write-only scopes
- **Combined operations**: Use only specific required scopes

## Core Modules

### Messages

```python
# Send a message with an embed
from arcade_discord import send_message, Embed

embed = Embed(
    title="Important Announcement",
    description="This is an important update",
    color=0x3498db  # Blue color
)

send_message(channel_id="123456789012345678", embed=embed)

# Get recent messages
messages = list_messages(channel_id="123456789012345678", limit=10)
```

### Channels

```python
# Create a new channel
from arcade_discord import create_channel, ChannelType

channel = create_channel(
    server_id="123456789012345678",
    name="announcements",
    type=ChannelType.ANNOUNCEMENT,
    topic="Official announcements"
)

# List channels
channels = list_channels(server_id="123456789012345678")
```

### Webhooks

```python
# Create and use a webhook
from arcade_discord import create_webhook, send_webhook_message

webhook = create_webhook(
    channel_id="123456789012345678",
    name="Auto-Updates"
)

send_webhook_message(
    webhook_url=webhook["url"],
    content="New update available!",
    username="Update Bot",
    avatar_url="https://example.com/avatar.png"
)
```

### Example Tools

```python
# Create a channel and post a message in one operation
from arcade_discord import create_and_post

result = create_and_post(
    server_id="123456789012345678",
    channel_name="welcome",
    message_content="Welcome to our server!"
)

# Create a webhook with test message
webhook = setup_webhook_integration(
    channel_id="123456789012345678",
    webhook_name="Alerts",
    test_message="Testing the webhook"
)

# Send a formatted message with fields
send_formatted_message(
    channel_id="123456789012345678",
    title="Weekly Update",
    description="Here's what happened this week:",
    fields={
        "New Features": "- Feature 1\n- Feature 2",
        "Bug Fixes": "- Fixed issue 1\n- Fixed issue 2"
    }
)
```

## Using Custom Types

```python
from arcade_discord import Embed, EmbedField, EmbedAuthor, EmbedFooter, EmbedImage

# Create a rich embed with strongly-typed components
embed = Embed(
    title="Rich Formatted Message",
    description="This is a demonstration of rich formatting",
    color=0x9b59b6,  # Purple
    fields=[
        EmbedField(name="Field 1", value="This is a field", inline=True),
        EmbedField(name="Field 2", value="Another field", inline=True)
    ],
    author=EmbedAuthor(
        name="Arcade AI",
        url="https://arcade.software",
        icon_url="https://example.com/icon.png"
    ),
    footer=EmbedFooter(text="Powered by Arcade Discord Toolkit"),
    image=EmbedImage(url="https://example.com/image.png")
)
```

## Error Handling

```python
from arcade_discord import send_message
from arcade_discord.exceptions import (
    DiscordValidationError,
    DiscordRateLimitError,
    DiscordPermissionError
)

try:
    send_message(channel_id="123456789012345678", content="Hello!")
except DiscordValidationError as e:
    print(f"Validation error: {e.message}")
except DiscordRateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except DiscordPermissionError as e:
    print(f"Permission error: {e}")
```

## Data Validation

```python
from arcade_discord import (
    validate_discord_id,
    validate_channel_name,
    validate_message_content,
    validate_embed,
    validate_webhook_url,
    validate_color
)

# Validate and normalize inputs
channel_id = validate_discord_id("123456789012345678", "channel_id")
channel_name = validate_channel_name("My Channel")  # Returns "my-channel"
validate_message_content(content="Hello, world!")
color = validate_color(0x3498db)  # Validates color range
```

## Developer Experience

- **Consistent parameter types**: Pre-defined types for consistency
- **Standardized error handling**: Descriptive exceptions with helpful messages
- **Predictable return formats**: Consistent response patterns
- **Strong validation**: Automatic validation with helpful error messages
- **Type safety**: Pydantic models and strong typing throughout
- **Automated normalization**: Inputs automatically normalized when possible

## Contributor Guidelines

If you're adding new tools to this toolkit, follow these standardized patterns:

### Tool Definition Structure

```python
@tool(requires_auth=Discord(scopes=SCOPE_CONSTANTS))
async def tool_name(
    context: ToolContext,
    required_param: Annotated[str, "Description of required parameter"],
    optional_param: Annotated[Optional[str], "Description of optional parameter"] = None,
) -> Annotated[Dict, "Description of return value"]:
    """One-line summary of what the tool does.

    More detailed description of functionality.

    Args:
        context: Tool execution context
        required_param: Description of required parameter
        optional_param: Description of optional parameter

    Examples:
        ```python
        # Example usage with comment
        tool_name(
            required_param="example_value",
            optional_param="optional_value"
        )
        ```

    Returns:
        Dict containing:
        - key1: Description of first return value
        - key2: Description of second return value
    """
    # Implementation
```

### Standardization Guidelines

1. **Tool Decorators**: One line with compact auth definition
2. **Docstrings**: Follow Args/Examples/Returns format with blank lines between sections
3. **Import Order**: Standard library → Arcade imports → Package imports
4. **Parameter Validation**: Use validation functions at the start of each tool
5. **Comments**: Include section comments for logical sections of code
6. **Return Values**: Use response templates for consistent return structures

Reference the `decorator_template.py` file for complete examples and patterns.

## Documentation

For detailed API documentation, see the [discord.md](discord.md) file. 
