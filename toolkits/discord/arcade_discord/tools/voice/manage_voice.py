"""Discord voice channel management tools.

This module provides tools for managing voice channels and interactions,
including creating, configuring, and monitoring voice channels.
"""

import logging
from typing import Annotated, Dict, Optional

from arcade.core.tool import tool
from arcade.core.tool_context import ToolContext
from arcade.providers.discord import Discord

from ...auth import CHANNEL_SCOPES, SERVER_SCOPES, VOICE_SCOPES
from ...client import get_discord_client
from ...exceptions import DiscordPermissionError, DiscordValidationError

logger = logging.getLogger(__name__)

# Voice channel types
VOICE_CHANNEL = 2
STAGE_CHANNEL = 13


@tool(
    requires_auth=Discord(
        scopes=VOICE_SCOPES + CHANNEL_SCOPES,
    )
)
async def voice_channel_info(
    context: ToolContext,
    server_id: Annotated[str, "ID of the server to get voice channel information from"],
    channel_id: Annotated[Optional[str], "ID of a specific voice channel to get info for"] = None,
) -> Annotated[Dict, "Information about voice channels and active voice connections"]:
    """
    Get information about voice channels and active voice connections in a server.

    This tool provides details about voice channels including who is connected to each,
    whether users are muted or deafened, and when they joined. For stage channels,
    it includes information about speakers and listeners.

    You can either get information about all voice channels in a server or focus on
    a specific voice channel by providing its ID.

    Examples:
    - Monitor who's currently in voice channels across a server
    - Check how many people are in a specific voice meeting
    - Get details about speakers and audience in a stage event

    Returns a dictionary with details about voice channels and their current participants.
    """
    client = await get_discord_client(context)

    try:
        # Get server voice states
        guild = await client.get_guild(server_id, with_counts=True)
        voice_states = guild.get("voice_states", [])

        # Get all channels to filter for voice channels
        channels = await client.get_guild_channels(server_id)
        voice_channels = [
            channel for channel in channels if channel.get("type") in [VOICE_CHANNEL, STAGE_CHANNEL]
        ]

        # If specific channel requested, filter for it
        if channel_id:
            voice_channels = [c for c in voice_channels if c.get("id") == channel_id]
            if not voice_channels:
                raise DiscordValidationError(
                    message=f"Voice channel {channel_id} not found in server {server_id}",
                    developer_message="Specified voice channel not found",
                )

        # Map voice states to channels
        channel_voice_states = {}
        for state in voice_states:
            channel_id = state.get("channel_id")
            if channel_id:
                if channel_id not in channel_voice_states:
                    channel_voice_states[channel_id] = []
                channel_voice_states[channel_id].append(state)

        # Build response with channels and their voice states
        result = {
            "server_id": server_id,
            "server_name": guild.get("name"),
            "voice_channels": [],
            "total_voice_users": len(voice_states),
        }

        for channel in voice_channels:
            channel_id = channel.get("id")
            states = channel_voice_states.get(channel_id, [])

            # Get user details for each voice state
            participants = []
            for state in states:
                user_id = state.get("user_id")
                try:
                    member = await client.get_guild_member(server_id, user_id)
                    user = member.get("user", {})

                    participants.append({
                        "user_id": user_id,
                        "username": user.get("username"),
                        "discriminator": user.get("discriminator"),
                        "nickname": member.get("nick"),
                        "self_mute": state.get("self_mute", False),
                        "self_deaf": state.get("self_deaf", False),
                        "server_mute": state.get("mute", False),
                        "server_deaf": state.get("deaf", False),
                        "is_video": state.get("self_video", False),
                        "is_streaming": state.get("self_stream", False),
                    })
                except Exception as e:
                    logger.warning(f"Failed to get member info for {user_id}: {e!s}")
                    participants.append({"user_id": user_id, "error": "Failed to get user details"})

            # Add channel info with participants
            channel_info = {
                "id": channel_id,
                "name": channel.get("name"),
                "type": "stage" if channel.get("type") == STAGE_CHANNEL else "voice",
                "bitrate": channel.get("bitrate"),
                "user_limit": channel.get("user_limit", 0),
                "rtc_region": channel.get("rtc_region"),
                "participants": participants,
                "participant_count": len(participants),
            }

            result["voice_channels"].append(channel_info)

        # Add summary counts
        result["voice_channel_count"] = len(result["voice_channels"])

        return result

    except Exception as e:
        logger.error(f"Failed to get voice channel info: {e!s}")
        raise DiscordPermissionError(
            message=f"Could not get voice channel info for server {server_id}",
            developer_message=f"Failed to get voice channel info: {e!s}",
        )


@tool(
    requires_auth=Discord(
        scopes=VOICE_SCOPES + CHANNEL_SCOPES,
    )
)
async def update_voice_channel(
    context: ToolContext,
    channel_id: Annotated[str, "ID of the voice channel to update"],
    name: Annotated[Optional[str], "New name for the voice channel"] = None,
    bitrate: Annotated[Optional[int], "New bitrate for the voice channel (8000-128000)"] = None,
    user_limit: Annotated[Optional[int], "New user limit (0-99, 0 for unlimited)"] = None,
    region: Annotated[Optional[str], "Voice region override (or 'automatic')"] = None,
) -> Annotated[Dict, "Updated voice channel details"]:
    """
    Update the settings of a Discord voice channel.

    This tool lets you modify various settings of voice channels including name,
    bitrate quality, user limit, and region. These settings affect the voice
    experience for users connecting to the channel.

    Voice channel settings:
    - name: Display name of the channel
    - bitrate: Audio quality (8000-128000 bps, higher is better quality)
    - user_limit: Maximum number of users (0-99, where 0 means unlimited)
    - region: Voice server region (specific region or 'automatic')

    Examples:
    - Increase bitrate for a high-quality music channel
    - Set user limit to create private voice rooms
    - Change region to reduce latency for users in specific areas

    Returns a dictionary with the updated voice channel details.
    """
    client = await get_discord_client(context)

    try:
        # Get current channel to verify it's a voice channel
        channel = await client.get_channel(channel_id)

        if channel.get("type") not in [VOICE_CHANNEL, STAGE_CHANNEL]:
            raise DiscordValidationError(
                message=f"Channel {channel_id} is not a voice channel",
                developer_message=f"Channel type {channel.get('type')} is not a voice channel type",
            )

        # Validate bitrate
        if bitrate is not None:
            if bitrate < 8000 or bitrate > 128000:
                raise DiscordValidationError(
                    message="Bitrate must be between 8000 and 128000",
                    developer_message="Invalid bitrate range",
                )

        # Validate user limit
        if user_limit is not None:
            if user_limit < 0 or user_limit > 99:
                raise DiscordValidationError(
                    message="User limit must be between 0 and 99",
                    developer_message="Invalid user limit range",
                )

        # Prepare update payload
        update_payload = {}
        if name is not None:
            update_payload["name"] = name
        if bitrate is not None:
            update_payload["bitrate"] = bitrate
        if user_limit is not None:
            update_payload["user_limit"] = user_limit
        if region is not None:
            update_payload["rtc_region"] = None if region.lower() == "automatic" else region

        # Update the channel
        updated_channel = await client.modify_channel(
            channel_id=channel_id,
            **update_payload,
            reason="Voice channel update via Arcade Discord toolkit",
        )

        # Format response
        return {
            "id": updated_channel.get("id"),
            "name": updated_channel.get("name"),
            "type": "stage" if updated_channel.get("type") == STAGE_CHANNEL else "voice",
            "bitrate": updated_channel.get("bitrate"),
            "user_limit": updated_channel.get("user_limit", 0),
            "rtc_region": updated_channel.get("rtc_region"),
            "position": updated_channel.get("position"),
            "updated_fields": list(update_payload.keys()),
        }

    except Exception as e:
        logger.error(f"Failed to update voice channel: {e!s}")
        raise DiscordPermissionError(
            message=f"Could not update voice channel {channel_id}",
            developer_message=f"Failed to update voice channel: {e!s}",
        )


@tool(
    requires_auth=Discord(
        scopes=VOICE_SCOPES + MEMBER_SCOPES,
    )
)
async def manage_voice_users(
    context: ToolContext,
    server_id: Annotated[str, "ID of the server where voice users are being managed"],
    user_id: Annotated[str, "ID of the user to manage in voice"],
    channel_id: Annotated[
        Optional[str], "ID of voice channel to move user to (None to disconnect)"
    ] = None,
    server_mute: Annotated[Optional[bool], "Whether to server-mute the user"] = None,
    server_deafen: Annotated[Optional[bool], "Whether to server-deafen the user"] = None,
) -> Annotated[Dict, "Result of the voice user management action"]:
    """
    Manage voice users by moving, muting, deafening, or disconnecting them.

    This tool gives you control over users in voice channels, allowing you to:
    - Move users between voice channels
    - Disconnect users from voice
    - Server-mute users (prevent them from speaking)
    - Server-deafen users (prevent them from hearing others)

    Note that these actions require appropriate permissions in the server and
    can only be performed on users who are already connected to a voice channel.

    Examples:
    - Move disruptive users to a moderation channel
    - Disconnect users who are AFK or inactive
    - Mute users who are causing audio issues
    - Move a user to a different team voice channel

    Returns a dictionary with the results of the voice management action.
    """
    client = await get_discord_client(context)

    try:
        # Get current voice state to confirm user is in a voice channel
        guild = await client.get_guild(server_id)
        voice_states = guild.get("voice_states", [])

        user_voice_state = next((vs for vs in voice_states if vs.get("user_id") == user_id), None)

        if not user_voice_state and channel_id is not None:
            # User isn't in voice but we're trying to move them
            raise DiscordValidationError(
                message=f"User {user_id} is not currently in a voice channel",
                developer_message="Cannot modify voice state of user not in voice",
            )

        # If channel_id is None, we're disconnecting the user
        # If it's set, we're moving them

        # If we're changing server_mute or server_deafen, we need to modify the guild member
        if server_mute is not None or server_deafen is not None:
            modify_payload = {}

            if server_mute is not None:
                modify_payload["mute"] = server_mute

            if server_deafen is not None:
                modify_payload["deaf"] = server_deafen

            await client.modify_guild_member(
                guild_id=server_id,
                user_id=user_id,
                **modify_payload,
                reason="Voice state modified via Arcade Discord toolkit",
            )

        # If we're moving or disconnecting, modify the voice state
        if user_voice_state or channel_id:
            await client.modify_user_voice_state(
                guild_id=server_id,
                user_id=user_id,
                channel_id=channel_id,  # None will disconnect
                reason="Voice state modified via Arcade Discord toolkit",
            )

        # Get updated voice state
        updated_guild = await client.get_guild(server_id)
        updated_voice_states = updated_guild.get("voice_states", [])
        updated_user_voice_state = next(
            (vs for vs in updated_voice_states if vs.get("user_id") == user_id), None
        )

        # Format response
        result = {
            "user_id": user_id,
            "server_id": server_id,
        }

        if updated_user_voice_state:
            # User is still in voice
            result["current_voice_state"] = {
                "channel_id": updated_user_voice_state.get("channel_id"),
                "server_mute": updated_user_voice_state.get("mute", False),
                "server_deafen": updated_user_voice_state.get("deaf", False),
                "self_mute": updated_user_voice_state.get("self_mute", False),
                "self_deaf": updated_user_voice_state.get("self_deaf", False),
            }

            if channel_id:
                result["action"] = "moved"
            else:
                result["action"] = "modified"
        else:
            # User is not in voice
            result["current_voice_state"] = None
            result["action"] = "disconnected"

        # Add what was changed
        result["changes"] = {}
        if channel_id is not None:
            result["changes"]["channel_id"] = channel_id
        if server_mute is not None:
            result["changes"]["server_mute"] = server_mute
        if server_deafen is not None:
            result["changes"]["server_deafen"] = server_deafen

        return result

    except Exception as e:
        logger.error(f"Failed to manage voice user: {e!s}")
        raise DiscordPermissionError(
            message=f"Could not manage voice state for user {user_id}",
            developer_message=f"Failed to manage voice user: {e!s}",
        )


@tool(
    requires_auth=Discord(
        scopes=VOICE_SCOPES + CHANNEL_SCOPES + SERVER_SCOPES,
    )
)
async def create_stage_event(
    context: ToolContext,
    server_id: Annotated[str, "ID of the server to create the stage event in"],
    channel_id: Annotated[str, "ID of the stage channel to use"],
    topic: Annotated[str, "Topic of the stage event (1-120 characters)"],
    scheduled_start_time: Annotated[Optional[str], "ISO timestamp when the event starts"] = None,
    scheduled_end_time: Annotated[Optional[str], "ISO timestamp when the event ends"] = None,
    description: Annotated[
        Optional[str], "Description of the event (up to 1000 characters)"
    ] = None,
) -> Annotated[Dict, "Details of the created stage event"]:
    """
    Create a stage event in a Discord stage channel.

    This tool allows you to create and schedule stage events, which are public
    presentations where speakers can address an audience. Stage events can be
    scheduled in advance or started immediately.

    You can set a topic, description, and optionally schedule start and end times
    for the event. Users can see upcoming stage events in the server.

    Examples:
    - Create an immediate AMA (Ask Me Anything) session
    - Schedule a future community announcement
    - Host a live tutorial or learning session
    - Set up a panel discussion with multiple speakers

    Returns a dictionary with details about the created stage event.
    """
    client = await get_discord_client(context)

    try:
        # Verify the channel is a stage channel
        channel = await client.get_channel(channel_id)

        if channel.get("type") != STAGE_CHANNEL:
            raise DiscordValidationError(
                message=f"Channel {channel_id} is not a stage channel",
                developer_message=f"Channel type {channel.get('type')} is not a stage channel",
            )

        # Validate the topic
        if not topic or len(topic) < 1 or len(topic) > 120:
            raise DiscordValidationError(
                message="Topic must be between 1 and 120 characters",
                developer_message="Invalid topic length",
            )

        # Create the stage instance
        stage_instance = await client.create_stage_instance(
            channel_id=channel_id,
            topic=topic,
            privacy_level=1,  # 1 = public (visible in stage discovery)
            send_start_notification=True,  # Notify users
            reason="Stage event created via Arcade Discord toolkit",
        )

        # If we have scheduled times, create a guild scheduled event
        scheduled_event = None
        if scheduled_start_time:
            event_payload = {
                "name": topic,
                "entity_type": 1,  # Stage instance
                "channel_id": channel_id,
                "scheduled_start_time": scheduled_start_time,
                "privacy_level": 2,  # Guild only
            }

            if scheduled_end_time:
                event_payload["scheduled_end_time"] = scheduled_end_time

            if description:
                event_payload["description"] = description

            scheduled_event = await client.create_guild_scheduled_event(
                guild_id=server_id, **event_payload
            )

        # Format response
        result = {
            "stage_instance": {
                "id": stage_instance.get("id"),
                "channel_id": stage_instance.get("channel_id"),
                "topic": stage_instance.get("topic"),
                "privacy_level": "public"
                if stage_instance.get("privacy_level") == 1
                else "private",
            },
            "server_id": server_id,
        }

        if scheduled_event:
            result["scheduled_event"] = {
                "id": scheduled_event.get("id"),
                "name": scheduled_event.get("name"),
                "description": scheduled_event.get("description"),
                "start_time": scheduled_event.get("scheduled_start_time"),
                "end_time": scheduled_event.get("scheduled_end_time"),
                "status": scheduled_event.get("status"),
            }

        return result

    except Exception as e:
        logger.error(f"Failed to create stage event: {e!s}")
        raise DiscordPermissionError(
            message=f"Could not create stage event in channel {channel_id}",
            developer_message=f"Failed to create stage event: {e!s}",
        )
