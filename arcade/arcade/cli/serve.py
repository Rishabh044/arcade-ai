import asyncio
import logging
import os
import sys
import threading
from contextlib import asynccontextmanager
from typing import Any

from loguru import logger

from arcade.core.schema import FullyQualifiedName
from arcade.core.telemetry import OTELHandler

try:
    import fastapi
except ImportError:
    raise ImportError(
        "FastAPI is not installed. Please install it using `pip install arcade-ai[fastapi]`."
    )

try:
    import uvicorn
except ImportError:
    raise ImportError(
        "Uvicorn is not installed. Please install it using `pip install arcade-ai[fastapi]`."
    )

from arcade.actor.fastapi.actor import FastAPIActor
from arcade.core.toolkit import Toolkit


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno  # type: ignore[assignment]

        # Find caller from where originated the logged message
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging(log_level: int = logging.INFO) -> None:
    # Intercept everything at the root logger
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(log_level)

    # Remove every other logger's handlers
    # and propagate to root logger
    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # Configure loguru with custom format, no colors
    logger.configure(
        handlers=[
            {
                "sink": sys.stdout,
                "serialize": False,
                "level": log_level,
                "format": "{level}  [{time:HH:mm:ss.SSS}] {message}"
                + (" {name}:{function}:{line}" if log_level <= logging.DEBUG else "")
                + ("\n{exception}" if "{exception}" in "{message}" else ""),
            }
        ]
    )


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):  # type: ignore[no-untyped-def]
    try:
        yield
    except asyncio.CancelledError:
        # This is necessary to prevent an unhandled error
        # when the user presses Ctrl+C
        logger.debug("Lifespan cancelled.")


class ToolkitWatcher:
    def __init__(
        self,
        initial: list[Toolkit],
        actor: FastAPIActor,
        shutdown_event: threading.Event,
    ):
        self.current_tools: list[FullyQualifiedName] = self._list_tools(initial)
        self.actor = actor
        self.shutdown_event = shutdown_event

    async def start(self, interval: int = 1) -> None:
        while not self.shutdown_event.is_set():
            try:
                new_toolkits = Toolkit.find_all_arcade_toolkits()
                new_tools = self._list_tools(new_toolkits)
                if new_tools != self.current_tools:
                    logger.info("Toolkit changes detected. Updating actor's catalog...")

                    for tool in new_tools:
                        if tool not in self.current_tools:
                            logger.info(f"New tool added:  {tool}")

                    for tool in self.current_tools:
                        if tool not in new_tools:
                            logger.info(f"Toolkit removed: {tool}")

                    self.actor.new_catalog()
                    for toolkit in new_toolkits:
                        self.actor.register_toolkit(toolkit)

                    self.current_tools = new_tools

                    logger.info("Actor's catalog has been updated.")
                else:
                    pass

            except Exception:
                logger.exception("Error while polling toolkits")

            await asyncio.sleep(interval)

    def _list_tools(self, toolkits: list[Toolkit]) -> list[FullyQualifiedName]:
        tools_list = []
        for toolkit in toolkits:
            for _, tools in toolkit.tools.items():
                if len(tools) != 0:
                    tools_list.extend([
                        FullyQualifiedName(tool, toolkit.name, toolkit.version) for tool in tools
                    ])
        return tools_list


def serve_default_actor(
    host: str = "127.0.0.1",
    port: int = 8002,
    disable_auth: bool = False,
    workers: int = 1,
    timeout_keep_alive: int = 5,
    enable_otel: bool = False,
    debug: bool = False,
    **kwargs: Any,
) -> None:
    """
    Get an instance of a FastAPI server with the Arcade Actor.
    """
    # Setup unified logging
    setup_logging(log_level=logging.DEBUG if debug else logging.INFO)

    toolkits = Toolkit.find_all_arcade_toolkits()
    if not toolkits:
        logger.error("No toolkits found in Python environment. Exiting...")
        return
    else:
        logger.info("Serving the following toolkits:")
        for toolkit in toolkits:
            logger.info(f"  - {toolkit.name} ({toolkit.package_name}): {len(toolkit.tools)} tools")

    actor_secret = os.environ.get("ARCADE_ACTOR_SECRET")
    if not disable_auth and not actor_secret:
        logger.warning(
            "Warning: ARCADE_ACTOR_SECRET environment variable is not set. Using 'dev' as the actor secret.",
        )
        actor_secret = actor_secret or "dev"

    app = fastapi.FastAPI(
        title="Arcade AI Actor",
        description="Arcade AI default Actor implementation using FastAPI.",
        version="0.1.0",
        lifespan=lifespan,  # Use custom lifespan to catch errors, notably KeyboardInterrupt (Ctrl+C)
    )

    otel_handler = OTELHandler(app, enable=enable_otel)

    actor = FastAPIActor(
        app, secret=actor_secret, disable_auth=disable_auth, otel_meter=otel_handler.get_meter()
    )
    for toolkit in toolkits:
        actor.register_toolkit(toolkit)

    shutdown_event = threading.Event()

    toolkit_watcher = ToolkitWatcher(toolkits, actor, shutdown_event)

    def run_polling() -> None:
        asyncio.run(toolkit_watcher.start())

    polling_thread = threading.Thread(target=run_polling, daemon=True)
    polling_thread.start()

    logger.info("Starting FastAPI server...")

    class CustomUvicornServer(uvicorn.Server):
        def install_signal_handlers(self) -> None:
            pass  # Disable Uvicorn's default signal handlers

    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        workers=workers,
        timeout_keep_alive=timeout_keep_alive,
        log_config=None,
        **kwargs,
    )
    server = CustomUvicornServer(config=config)

    async def serve() -> None:
        await server.serve()

    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")
    finally:
        if enable_otel:
            otel_handler.shutdown()
        shutdown_event.set()
        polling_thread.join(timeout=5)
        logger.debug("Server shutdown complete.")
