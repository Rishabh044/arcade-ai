"""Discord Gateway API implementation for real-time events and websocket connections."""

import asyncio
import json
import logging
import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import aiohttp

from arcade.context import ToolContext
from arcade_discord.exceptions import DiscordGatewayError

logger = logging.getLogger(__name__)

# Discord Gateway API v10 URL
GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json"


class GatewayOpcodes(Enum):
    """Discord Gateway opcodes for different operations."""

    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    PRESENCE_UPDATE = 3
    VOICE_STATE_UPDATE = 4
    RESUME = 6
    RECONNECT = 7
    REQUEST_GUILD_MEMBERS = 8
    INVALID_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11


class GatewayConnection:
    """
    Manages a Discord Gateway websocket connection for real-time events.

    This class handles authentication, heartbeats, and event dispatching for
    maintaining a stable connection to Discord's Gateway API.
    """

    def __init__(self, context: ToolContext, intents: int = 513):
        """
        Initialize a new Gateway connection.

        Args:
            context: The Arcade tool context with authentication details
            intents: Discord Gateway intents bitfield (default: 513 for GUILDS and GUILD_MESSAGES)
        """
        self.context = context
        self.intents = intents
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.token = context.get_auth_value("token")

        # Connection state
        self.sequence: Optional[int] = None
        self.session_id: Optional[str] = None
        self.heartbeat_interval: Optional[float] = None
        self.last_heartbeat_ack: Optional[float] = None
        self.heartbeat_task: Optional[asyncio.Task] = None

        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}

        # Flags
        self.is_connected = False
        self.is_reconnecting = False
        self.should_reconnect = True

    async def connect(self) -> None:
        """Establish a connection to the Discord Gateway."""
        if self.is_connected:
            logger.warning("Already connected to Gateway")
            return

        self.session = aiohttp.ClientSession()
        self.should_reconnect = True

        try:
            self.ws = await self.session.ws_connect(GATEWAY_URL)
            logger.info("Connected to Discord Gateway")

            # Process initial HELLO message
            msg = await self.ws.receive()
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                if data["op"] == GatewayOpcodes.HELLO.value:
                    self.heartbeat_interval = data["d"]["heartbeat_interval"] / 1000
                    self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                    await self._identify()
                    self.is_connected = True

                    # Start the event processing loop
                    asyncio.create_task(self._event_loop())
                else:
                    raise DiscordGatewayError(
                        message="Expected HELLO as first Gateway message",
                        developer_message=f"Received unexpected opcode: {data['op']}",
                    )
        except Exception as e:
            logger.error(f"Failed to connect to Gateway: {e!s}")
            await self.close()
            raise DiscordGatewayError(
                message="Failed to connect to Discord Gateway", developer_message=str(e)
            )

    async def close(self) -> None:
        """Close the Gateway connection and clean up resources."""
        self.should_reconnect = False
        self.is_connected = False

        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            self.heartbeat_task = None

        if self.ws:
            await self.ws.close()
            self.ws = None

        if self.session:
            await self.session.close()
            self.session = None

        logger.info("Disconnected from Discord Gateway")

    async def _heartbeat_loop(self) -> None:
        """Send heartbeats at the specified interval to keep the connection alive."""
        while True:
            if not self.ws or self.ws.closed:
                logger.warning("Websocket closed, stopping heartbeat loop")
                break

            # Send heartbeat with sequence number
            await self._send_heartbeat()
            self.last_heartbeat_ack = None

            # Wait for the heartbeat interval
            await asyncio.sleep(self.heartbeat_interval)

            # Check if we received an ACK
            if self.last_heartbeat_ack is None and self.is_connected:
                logger.warning("No heartbeat ACK received, reconnecting")
                self.is_connected = False
                asyncio.create_task(self._reconnect())
                break

    async def _send_heartbeat(self) -> None:
        """Send a heartbeat to the Gateway server."""
        if not self.ws or self.ws.closed:
            return

        payload = {"op": GatewayOpcodes.HEARTBEAT.value, "d": self.sequence}
        await self.ws.send_json(payload)
        logger.debug(f"Sent heartbeat with sequence: {self.sequence}")

    async def _identify(self) -> None:
        """Send the identify payload to authenticate with Discord Gateway."""
        if not self.ws or self.ws.closed:
            return

        payload = {
            "op": GatewayOpcodes.IDENTIFY.value,
            "d": {
                "token": self.token,
                "intents": self.intents,
                "properties": {"$os": "linux", "$browser": "arcade", "$device": "arcade"},
            },
        }
        await self.ws.send_json(payload)
        logger.info("Sent identify payload to Gateway")

    async def _resume(self) -> None:
        """Resume a disconnected session."""
        if not self.session_id or not self.sequence:
            logger.warning("Cannot resume: missing session_id or sequence")
            return

        payload = {
            "op": GatewayOpcodes.RESUME.value,
            "d": {"token": self.token, "session_id": self.session_id, "seq": self.sequence},
        }
        await self.ws.send_json(payload)
        logger.info(f"Attempting to resume session {self.session_id}")

    async def _reconnect(self) -> None:
        """Handle reconnection logic for disconnects."""
        if self.is_reconnecting or not self.should_reconnect:
            return

        self.is_reconnecting = True
        retry_count = 0
        max_retries = 5

        while retry_count < max_retries and self.should_reconnect:
            try:
                await asyncio.sleep(min(5 * 2**retry_count, 60))  # Exponential backoff
                logger.info(f"Attempting to reconnect (attempt {retry_count + 1}/{max_retries})")

                # Close existing connection
                if self.ws:
                    await self.ws.close()

                # Create new connection
                self.ws = await self.session.ws_connect(GATEWAY_URL)

                # Process HELLO message
                msg = await self.ws.receive()
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    if data["op"] == GatewayOpcodes.HELLO.value:
                        self.heartbeat_interval = data["d"]["heartbeat_interval"] / 1000

                        # Try to resume if we have a session
                        if self.session_id and self.sequence:
                            await self._resume()
                        else:
                            # Otherwise identify as new
                            await self._identify()

                        # Restart heartbeat
                        if self.heartbeat_task:
                            self.heartbeat_task.cancel()
                        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

                        self.is_connected = True
                        self.is_reconnecting = False

                        # Restart the event loop
                        asyncio.create_task(self._event_loop())

                        logger.info("Successfully reconnected to Gateway")
                        break
            except Exception as e:
                logger.error(f"Failed to reconnect: {e!s}")
                retry_count += 1

        if retry_count >= max_retries and self.should_reconnect:
            logger.error(f"Failed to reconnect after {max_retries} attempts")
            self.is_reconnecting = False
            # Signal that we've had a fatal reconnection failure
            self.should_reconnect = False
            self.is_connected = False

    async def _event_loop(self) -> None:
        """Process incoming Gateway events."""
        while self.is_connected and self.ws and not self.ws.closed:
            try:
                msg = await self.ws.receive()

                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await self._handle_dispatch(data)
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    logger.warning("WebSocket was closed")
                    self.is_connected = False
                    if self.should_reconnect:
                        await self._reconnect()
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {msg.data}")
                    self.is_connected = False
                    if self.should_reconnect:
                        await self._reconnect()
                    break
            except Exception as e:
                logger.error(f"Error in Gateway event loop: {e!s}")
                if self.should_reconnect:
                    await self._reconnect()
                break

    async def _handle_dispatch(self, data: Dict[str, Any]) -> None:
        """Process a Gateway dispatch based on its opcode."""
        op = data.get("op")

        # Update sequence if present
        if data.get("s") is not None:
            self.sequence = data["s"]

        # Handle different opcodes
        if op == GatewayOpcodes.DISPATCH.value:
            event_type = data.get("t")
            event_data = data.get("d")

            # Store session ID from the READY event
            if event_type == "READY":
                self.session_id = event_data.get("session_id")
                logger.info(f"Received READY, session_id: {self.session_id}")

            # Dispatch to registered event handlers
            if event_type:
                await self._dispatch_event(event_type, event_data)

        elif op == GatewayOpcodes.HEARTBEAT.value:
            # Server requested an immediate heartbeat
            await self._send_heartbeat()

        elif op == GatewayOpcodes.RECONNECT.value:
            logger.info("Server requested reconnect")
            self.is_connected = False
            await self._reconnect()

        elif op == GatewayOpcodes.INVALID_SESSION.value:
            can_resume = data.get("d", False)
            if can_resume:
                logger.info("Invalid session but can resume, attempting to resume")
                await self._resume()
            else:
                logger.info("Invalid session, cannot resume, waiting to identify")
                self.session_id = None
                self.sequence = None
                await asyncio.sleep(2)
                await self._identify()

        elif op == GatewayOpcodes.HELLO.value:
            # Already handled in connect()
            pass

        elif op == GatewayOpcodes.HEARTBEAT_ACK.value:
            logger.debug("Received heartbeat ACK")
            self.last_heartbeat_ack = time.time()

    async def _dispatch_event(self, event_type: str, event_data: Any) -> None:
        """Dispatch an event to all registered handlers for that event type."""
        handlers = self.event_handlers.get(event_type, [])

        for handler in handlers:
            try:
                await handler(event_data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e!s}")

    def on(self, event_type: str) -> Callable:
        """
        Decorator to register an event handler for a specific event type.

        Args:
            event_type: The Discord event name (e.g., "MESSAGE_CREATE")

        Returns:
            Decorator function

        Example:
            ```python
            gateway = GatewayConnection(context)

            @gateway.on("MESSAGE_CREATE")
            async def on_message(data):
                print(f"New message: {data['content']}")
            ```
        """

        def decorator(func: Callable) -> Callable:
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            self.event_handlers[event_type].append(func)
            return func

        return decorator

    def add_event_handler(self, event_type: str, handler: Callable) -> None:
        """
        Register an event handler function for a specific event type.

        Args:
            event_type: The Discord event name (e.g., "MESSAGE_CREATE")
            handler: Async function that takes event data as parameter
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def remove_event_handler(self, event_type: str, handler: Callable) -> None:
        """
        Remove an event handler function for a specific event type.

        Args:
            event_type: The Discord event name
            handler: The handler function to remove
        """
        if event_type in self.event_handlers:
            self.event_handlers[event_type] = [
                h for h in self.event_handlers[event_type] if h != handler
            ]


# Discord Gateway intents
class GatewayIntents:
    """Discord Gateway intents for specifying what events to receive."""

    GUILDS = 1 << 0
    GUILD_MEMBERS = 1 << 1
    GUILD_BANS = 1 << 2
    GUILD_EMOJIS_AND_STICKERS = 1 << 3
    GUILD_INTEGRATIONS = 1 << 4
    GUILD_WEBHOOKS = 1 << 5
    GUILD_INVITES = 1 << 6
    GUILD_VOICE_STATES = 1 << 7
    GUILD_PRESENCES = 1 << 8
    GUILD_MESSAGES = 1 << 9
    GUILD_MESSAGE_REACTIONS = 1 << 10
    GUILD_MESSAGE_TYPING = 1 << 11
    DIRECT_MESSAGES = 1 << 12
    DIRECT_MESSAGE_REACTIONS = 1 << 13
    DIRECT_MESSAGE_TYPING = 1 << 14
    MESSAGE_CONTENT = 1 << 15
    GUILD_SCHEDULED_EVENTS = 1 << 16
    AUTO_MODERATION_CONFIGURATION = 1 << 20
    AUTO_MODERATION_EXECUTION = 1 << 21

    @classmethod
    def all(cls) -> int:
        """Get all intents combined."""
        return (
            cls.GUILDS
            | cls.GUILD_MEMBERS
            | cls.GUILD_BANS
            | cls.GUILD_EMOJIS_AND_STICKERS
            | cls.GUILD_INTEGRATIONS
            | cls.GUILD_WEBHOOKS
            | cls.GUILD_INVITES
            | cls.GUILD_VOICE_STATES
            | cls.GUILD_PRESENCES
            | cls.GUILD_MESSAGES
            | cls.GUILD_MESSAGE_REACTIONS
            | cls.GUILD_MESSAGE_TYPING
            | cls.DIRECT_MESSAGES
            | cls.DIRECT_MESSAGE_REACTIONS
            | cls.DIRECT_MESSAGE_TYPING
            | cls.MESSAGE_CONTENT
            | cls.GUILD_SCHEDULED_EVENTS
            | cls.AUTO_MODERATION_CONFIGURATION
            | cls.AUTO_MODERATION_EXECUTION
        )

    @classmethod
    def default(cls) -> int:
        """Get default intents (GUILDS and GUILD_MESSAGES)."""
        return cls.GUILDS | cls.GUILD_MESSAGES | cls.MESSAGE_CONTENT

    @classmethod
    def none(cls) -> int:
        """Get no intents."""
        return 0
