"""Templates for Discord toolkit tool decorators and docstrings.

This module provides standardized patterns for tool definitions to ensure
consistent formatting and documentation across the entire toolkit.
"""


# ---------------------- Tool Decorator Template ----------------------
# Replace SCOPE_CONSTANTS with appropriate scopes from utils.py
#
# @tool(requires_auth=Discord(scopes=SCOPE_CONSTANTS))
# async def tool_name(
#     context: ToolContext,
#     param1: Annotated[str, "Description of param1"],
#     param2: Annotated[int, "Description of param2"],
#     optional_param: Annotated[Optional[str], "Description of optional_param"] = None,
# ) -> Annotated[Dict, "Description of return value"]:
#     """One-line summary of what the tool does.
#
#     More detailed description of the tool functionality,
#     context, and purpose.
#
#     Args:
#         context: Tool execution context
#         param1: Description of first parameter
#         param2: Description of second parameter
#         optional_param: Description of optional parameter
#
#     Examples:
#         ```python
#         # Example usage comment
#         tool_name(
#             param1="example_value",
#             param2=42,
#             optional_param="optional_value"
#         )
#         ```
#
#     Returns:
#         Dict containing:
#         - key1: Description of first return value
#         - key2: Description of second return value
#     """
#     # Implementation here
#     pass


# ---------------------- Example Message Tool ----------------------
# Example of a correctly formatted tool for sending a message

# @tool(requires_auth=Discord(scopes=MESSAGE_WRITE_SCOPES))
# async def example_message_tool(
#     context: ToolContext,
#     channel_id: Annotated[str, "ID of the channel to send the message to"],
#     content: Annotated[str, "Text content of the message"],
# ) -> Annotated[Dict, "Details of the sent message"]:
#     """Send a message to a Discord channel.
#
#     Sends a text message to the specified Discord channel
#     with the given content.
#
#     Args:
#         context: Tool execution context
#         channel_id: ID of the Discord channel
#         content: Text content to send
#
#     Examples:
#         ```python
#         # Send a simple message
#         example_message_tool(
#             channel_id="123456789012345678",
#             content="Hello, Discord!"
#         )
#         ```
#
#     Returns:
#         Dict containing:
#         - message_id: ID of the sent message
#         - content: Content of the message
#         - timestamp: When the message was sent
#     """
#     # Implementation would go here
#     pass


# ---------------------- Example Channel Tool ----------------------
# Example of a correctly formatted tool for creating a channel

# @tool(requires_auth=Discord(scopes=CHANNEL_WRITE_SCOPES))
# async def example_channel_tool(
#     context: ToolContext,
#     server_id: Annotated[str, "ID of the server to create the channel in"],
#     name: Annotated[str, "Name of the channel"],
#     type: Annotated[ChannelType, "Type of channel to create"],
# ) -> Annotated[Dict, "Details of the created channel"]:
#     """Create a channel in a Discord server.
#
#     Creates a new channel of the specified type in the
#     target Discord server.
#
#     Args:
#         context: Tool execution context
#         server_id: ID of the Discord server
#         name: Name for the new channel
#         type: Type of channel to create
#
#     Examples:
#         ```python
#         # Create a text channel
#         example_channel_tool(
#             server_id="123456789012345678",
#             name="general-chat",
#             type=ChannelType.TEXT
#         )
#         ```
#
#     Returns:
#         Dict containing:
#         - id: ID of the created channel
#         - name: Name of the channel
#         - type: Type of the channel
#     """
#     # Implementation would go here
#     pass
