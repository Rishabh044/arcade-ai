import asyncio
import os
import threading
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Optional
from urllib.parse import parse_qs, urlencode

import toml
import typer
from openai.resources.chat.completions import ChatCompletionChunk, Stream
from rich.console import Console
from rich.markdown import Markdown
from rich.markup import escape
from rich.table import Table
from rich.text import Text
from typer.core import TyperGroup
from typer.models import Context

from arcade.cli.page_content import LOGIN_FAILED_HTML, LOGIN_SUCCESS_HTML
from arcade.core.catalog import ToolCatalog
from arcade.core.client import EngineClient
from arcade.core.schema import ToolCallOutput, ToolContext
from arcade.core.toolkit import Toolkit


class OrderCommands(TyperGroup):
    def list_commands(self, ctx: Context) -> list[str]:  # type: ignore[override]
        """Return list of commands in the order appear."""
        return list(self.commands)  # get commands using self.commands


console = Console()
cli = typer.Typer(
    cls=OrderCommands,
)

httpd: HTTPServer | None = None


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, state: str, **kwargs):  # type: ignore[no-untyped-def]
        self.state = state  # Simple CSRF protection
        super().__init__(*args, **kwargs)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 Argument `format` is shadowing a Python builtin
        # Override to suppress logging to stdout
        pass

    def _parse_login_response(self) -> tuple[str, str, str] | None:
        # Parse the query string from the URL
        query_string = self.path.split("?", 1)[-1]
        params = parse_qs(query_string)
        returned_state = params.get("state", [None])[0]

        if returned_state != self.state:
            console.print(
                "❌ Login failed: Invalid login attempt. Please try again.", style="bold red"
            )
            return None

        api_key = params.get("api_key", [None])[0] or ""
        email = params.get("email", [None])[0] or ""
        warning = params.get("warning", [None])[0] or ""

        return api_key, email, warning

    def _handle_login_response(self) -> bool:
        result = self._parse_login_response()
        if result is None:
            return False
        api_key, email, warning = result

        if warning:
            console.print(warning, style="bold yellow")

        # If API key and email are received, store them in a file
        if not api_key or not email:
            console.print(
                "❌ Login failed: No credentials received. Please try again.", style="bold red"
            )
            return False

        # TODO don't overwrite existing config
        config_file_path = os.path.expanduser("~/.arcade/arcade.toml")
        new_config = {"api": {"key": api_key}, "user": {"email": email}}
        with open(config_file_path, "w") as f:
            toml.dump(new_config, f)

        # Send a success response to the browser
        console.print(
            f"""✅ Hi there, {email}!

Your Arcade API key is: {api_key}
Stored in: {config_file_path}""",
            style="bold green",
        )
        return True

    def do_GET(self) -> None:
        success = self._handle_login_response()
        if success:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(LOGIN_SUCCESS_HTML)
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(LOGIN_FAILED_HTML)

        # Always shut down the server so it doesn't keep running
        threading.Thread(target=shutdown_server).start()


def shutdown_server() -> None:
    # Shut down the server gracefully
    global httpd
    if "httpd" in globals() and httpd:
        httpd.shutdown()


def run_server(state: str) -> None:
    # Initialize and run the server
    global httpd
    server_address = ("", 9905)
    handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, state=state, **kwargs)
    httpd = HTTPServer(server_address, handler)
    httpd.serve_forever()


@cli.command(help="Log in to Arcade Cloud")
def login() -> None:
    """
    Logs the user into Arcade Cloud.
    """

    # If ~/.arcade/arcade.toml exists, load the API key and email
    config_file_path = os.path.expanduser("~/.arcade/arcade.toml")
    if os.path.exists(config_file_path):
        config = toml.load(config_file_path)
        api_key = config.get("api", {}).get("key")
        email = config.get("user", {}).get("email")
        if api_key and email:
            console.print(
                f"You're already logged in as {email}. Delete {config_file_path} to log in as a different user."
            )
            return

    # Start the HTTP server in a new thread
    state = str(uuid.uuid4())
    server_thread = threading.Thread(target=run_server, args=(state,))
    server_thread.start()

    try:
        # Open the browser for user login
        callback_uri = "http://localhost:9905/callback"
        params = urlencode({"callback_uri": callback_uri, "state": state})
        login_url = f"https://cloud.arcade-ai.com/api/v1/auth/cli_login?{params}"
        console.print("Opening a browser to log you in...")
        webbrowser.open(login_url)

        # Wait for the server thread to finish
        server_thread.join()
    except KeyboardInterrupt:
        shutdown_server()
        if server_thread.is_alive():
            server_thread.join()  # Ensure the server thread completes and cleans up


@cli.command(help="Log out of Arcade Cloud")
def logout() -> None:
    """
    Logs the user out of Arcade Cloud.
    """

    # If ~/.arcade/arcade.toml exists, delete it
    config_file_path = os.path.expanduser("~/.arcade/arcade.toml")
    if os.path.exists(config_file_path):
        os.remove(config_file_path)
        console.print("You're now logged out.", style="bold")
    else:
        console.print("You're not logged in.", style="bold red")


@cli.command(help="Create a new toolkit package directory")
def new(
    directory: str = typer.Option(os.getcwd(), "--dir", help="tools directory path"),
) -> None:
    """
    Creates a new toolkit with the given name, description, and result type.
    """
    from arcade.cli.new import create_new_toolkit

    try:
        create_new_toolkit(directory)
    except Exception as e:
        error_message = f"❌ Failed to create new Toolkit: {escape(str(e))}"
        console.print(error_message, style="bold red")


@cli.command(help="Show the available tools in an actor or toolkit directory")
def show(
    toolkit: Optional[str] = typer.Option(
        None, "-t", "--toolkit", help="The toolkit to show the tools of"
    ),
    actor: Optional[str] = typer.Option(None, help="A running actor address to list tools from"),
) -> None:
    """
    Show the available tools in an actor or toolkit
    """

    try:
        catalog = create_cli_catalog(toolkit=toolkit)

        # Create a table with Rich library
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name")
        table.add_column("Description")
        table.add_column("Toolkit")
        table.add_column("Version")

        for tool in catalog:
            table.add_row(tool.name, tool.description, tool.meta.toolkit, tool.version)

        console.print(table)

    except Exception as e:
        # better error message here
        error_message = f"❌ Failed to List tools: {escape(str(e))}"
        console.print(error_message, style="bold red")


@cli.command(help="Run a tool using an LLM to predict the arguments")
def run(
    toolkit: Optional[str] = typer.Option(
        None, "-t", "--toolkit", help="The toolkit to include in the run"
    ),
    model: str = typer.Option("gpt-4o", "-m", help="The model to use for prediction."),
    tool: str = typer.Option(None, "--tool", help="The name of the tool to run."),
    choice: str = typer.Option(
        "generate", "-c", "--choice", help="The value of the tool choice argument"
    ),
    stream: bool = typer.Option(
        False, "-s", "--stream", is_flag=True, help="Stream the tool output."
    ),
    prompt: str = typer.Argument(..., help="The prompt to use for context"),
) -> None:
    """
    Run a tool using an LLM to predict the arguments.
    """
    from arcade.core.client import EngineClient
    from arcade.core.executor import ToolExecutor

    try:
        # TODO: make the Config singleton not load immediately?
        from arcade.core.config import Config

        catalog = create_cli_catalog(toolkit=toolkit)

        tools = [catalog[tool]] if tool else list(catalog)

        config = Config.load_from_file()
        if not config.engine or not config.engine_url:
            console.print("❌ Engine configuration not found or URL is missing.", style="bold red")
            typer.Exit(code=1)

        if not config.api or not config.api.key:
            console.print(
                "❌ API configuration not found or key is missing. Please run `arcade login`.",
                style="bold red",
            )
            typer.Exit(code=1)
        client = EngineClient(api_key=config.api.key, base_url=config.engine_url)

        # TODO better way of doing this
        tool_choice = "auto" if choice in ["execute", "generate"] else choice
        calls = client.call_tool(tools, tool_choice=tool_choice, prompt=prompt, model=model)

        if len(calls) == 0:
            console.print("[bold red]No tools were called[/bold red]")

        messages = [
            {"role": "user", "content": prompt},
        ]

        for tool_name, parameters in calls:
            called_tool = catalog[tool_name]
            console.print(f"Calling tool: {tool_name} with params: {parameters}", style="bold blue")

            # TODO async.gather instead of loop.
            output: ToolCallOutput = asyncio.run(
                ToolExecutor.run(
                    called_tool.tool,
                    called_tool.definition,
                    called_tool.input_model,
                    called_tool.output_model,
                    ToolContext(),
                    **parameters,
                )
            )
            if output.error:
                console.print(output.error.message, style="bold red")
                typer.Exit(code=1)
            else:
                messages += [
                    {
                        "role": "assistant",
                        # TODO: escape the output and ensure serialization works
                        "content": f"Results of Tool {tool_name}: {output.value!s}",
                    },
                ]

        if choice == "execute":
            console.print(output.value, style="green")
            raise typer.Exit(0)
        else:
            if stream:
                stream_response = client.stream_complete(model=model, messages=messages)
                display_streamed_markdown(stream_response)
            else:
                response = client.complete(model=model, messages=messages)
                if not len(response.choices) and not response.choices[0].message.content:
                    console.print("No response from the tool.", style="bold red")
                else:
                    console.print(Markdown(response.choices[0].message.content or ""))

    except RuntimeError as e:
        error_message = f"❌ Failed to run tool{': ' + escape(str(e)) if str(e) else ''}"
        console.print(error_message, style="bold red")


@cli.command(help="Chat with a language model")
def chat(
    model: str = typer.Option("gpt-4o", "-m", help="The model to use for prediction."),
    stream: bool = typer.Option(
        True, "-s", "--stream", is_flag=True, help="Stream the tool output."
    ),
) -> None:
    """
    Chat with a language model.
    """

    # TODO: make the Config singleton not load immediately?
    from arcade.core.config import Config

    config = Config.load_from_file()
    if not config.engine or not config.engine_url:
        console.print("❌ Engine configuration not found or URL is missing.", style="bold red")
        typer.Exit(code=1)

    if not config.api or not config.api.key:
        console.print(
            "❌ API configuration not found or key is missing. Please run `arcade login`.",
            style="bold red",
        )
        typer.Exit(code=1)

    client = EngineClient(api_key=config.api.key, base_url=config.engine_url)

    if config.user and config.user.email:
        user_email = config.user.email
        user_attribution = f"({user_email})"
    else:
        console.print(
            "❌ User email not found in configuration. Please run `arcade login`.", style="bold red"
        )
        typer.Exit(code=1)

    try:
        # start messages conversation
        messages: list[dict[str, Any]] = []

        chat_header = Text.assemble(
            "\n",
            (
                "======== Arcade AI Chat ========",
                "bold magenta underline",
            ),
            "\n",
        )
        console.print(chat_header)

        while True:
            user_input = console.input(
                f"\n[magenta][bold]User[/bold] {user_attribution}:[/magenta] "
            )
            messages.append({"role": "user", "content": user_input})

            if stream:
                stream_response = client.stream_complete(
                    model=model,
                    messages=messages,
                    tool_choice="generate",
                    user=user_email,
                )
                role, message = display_streamed_markdown(stream_response)
                messages.append({"role": role, "content": message})
            else:
                response = client.complete(
                    model=model,
                    messages=messages,
                    tool_choice="generate",
                    user=user_email,
                )
                message_content = response.choices[0].message.content or ""
                role = response.choices[0].message.role

                if role == "assistant":
                    console.print("\n[bold blue]Assistant:[/bold blue] ", Markdown(message_content))
                else:
                    console.print(f"\n[bold magenta]{role}:[/bold magenta] {message_content}")

                messages.append({"role": role, "content": message_content})

    except KeyboardInterrupt:
        console.print("Chat stopped by user.", style="bold blue")
        typer.Exit()

    except RuntimeError as e:
        error_message = f"❌ Failed to run tool{': ' + escape(str(e)) if str(e) else ''}"
        console.print(error_message, style="bold red")
        raise typer.Exit()


@cli.command(help="Start an Actor server with specified configurations.")
def dev(
    host: str = typer.Option(
        "127.0.0.1", help="Host for the app, from settings by default.", show_default=True
    ),
    port: int = typer.Option("8000", help="Port for the app, defaults to ", show_default=True),
) -> None:
    """
    Starts the actor with host, port, and reload options. Uses
    Uvicorn as ASGI actor. Parameters allow runtime configuration.
    """
    from arcade.cli.serve import serve_default_actor

    try:
        serve_default_actor(host, port)
    except KeyboardInterrupt:
        console.print("actor stopped by user.", style="bold red")
        typer.Exit()
    except Exception as e:
        error_message = f"❌ Failed to start Arcade Actor: {escape(str(e))}"
        console.print(error_message, style="bold red")
        raise typer.Exit(code=1)


@cli.command(help="Manage the Arcade Engine (start/stop/restart)")
def engine(
    action: str = typer.Argument("start", help="The action to take (start/stop/restart)"),
    host: str = typer.Option("localhost", "--host", "-h", help="The host of the engine"),
    port: int = typer.Option(6901, "--port", "-p", help="The port of the engine"),
) -> None:
    """
    Manage the Arcade Engine (start/stop/restart)
    """
    raise NotImplementedError("This feature is not yet implemented.")


@cli.command(help="Manage credientials stored in the Arcade Engine")
def credentials(
    action: str = typer.Argument("show", help="The action to take (add/remove/show)"),
    name: str = typer.Option(None, "--name", "-n", help="The name of the credential to add/remove"),
    val: str = typer.Option(None, "--val", "-v", help="The value of the credential to add/remove"),
) -> None:
    """
    Manage credientials stored in the Arcade Engine
    """
    raise NotImplementedError("This feature is not yet implemented.")


@cli.command(help="Show/edit configuration details of the Arcade Engine")
def config(
    action: str = typer.Argument("show", help="The action to take (show/edit)"),
    key: str = typer.Option(
        None, "--key", "-k", help="The configuration key to edit (e.g., 'api.key')"
    ),
    val: str = typer.Option(None, "--val", "-v", help="The value of the configuration to edit"),
) -> None:
    """
    Show/edit configuration details of the Arcade Engine
    """

    # TODO: make the Config singleton not load immediately?
    from arcade.core.config import Config

    config = Config.load_from_file()

    if action == "show":
        display_config_as_table(config)
    elif action == "edit":
        if not key or val is None:
            console.print("❌ Key and value must be provided for editing.", style="bold red")
            raise typer.Exit(code=1)

        keys = key.split(".")
        if len(keys) != 2:
            console.print("❌ Invalid key format. Use 'section.name' format.", style="bold red")
            raise typer.Exit(code=1)

        section, name = keys
        section_dict = getattr(config, section, None)
        if section_dict and hasattr(section_dict, name):
            setattr(section_dict, name, val)
            config.save_to_file()
            console.print("✅ Configuration updated successfully.", style="bold green")
        else:
            console.print(
                f"❌ Invalid configuration name: {name} in section: {section}", style="bold red"
            )
            raise typer.Exit(code=1)
    else:
        console.print(f"❌ Invalid action: {action}", style="bold red")
        raise typer.Exit(code=1)


def display_config_as_table(config) -> None:  # type: ignore[no-untyped-def]
    """
    Display the configuration details as a table using Rich library.
    """
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Section")
    table.add_column("Name")
    table.add_column("Value")

    for section_name in config.model_dump():
        section = getattr(config, section_name)
        if section:
            section = section.dict()
            first = True
            for name, value in section.items():
                if first:
                    table.add_row(section_name, name, str(value))
                    first = False
                else:
                    table.add_row("", name, str(value))
            table.add_row("", "", "")

    console.print(table)


def display_streamed_markdown(stream: Stream[ChatCompletionChunk]) -> tuple[str, str]:
    """
    Display the streamed markdown chunks as a single line.
    """
    from rich.live import Live

    full_message = ""
    role = ""
    with Live(console=console, refresh_per_second=10) as live:
        for chunk in stream:
            choice = chunk.choices[0]
            chunk_message = choice.delta.content
            if role == "":
                role = choice.delta.role or ""
                if role == "assistant":
                    console.print("\n[bold blue]Assistant:[/bold blue] ")
            if chunk_message:
                full_message += chunk_message
                markdown_chunk = Markdown(full_message)
                live.update(markdown_chunk)
        return role, full_message


def create_cli_catalog(
    toolkit: str | None = None,
    show_toolkits: bool = False,
) -> ToolCatalog:
    """
    Load toolkits from the python environment.
    """
    if toolkit:
        try:
            prefixed_toolkit = "arcade_" + toolkit
            toolkits = [Toolkit.from_package(prefixed_toolkit)]
        except ValueError:
            try:  # try without prefix
                toolkits = [Toolkit.from_package(toolkit)]
            except ValueError as e:
                console.print(f"❌ {e}", style="bold red")
                typer.Exit(code=1)
    else:
        toolkits = Toolkit.find_all_arcade_toolkits()

    if not toolkits:
        console.print("❌ No toolkits found or specified", style="bold red")
        typer.Exit(code=1)

    catalog = ToolCatalog()
    for loaded_toolkit in toolkits:
        if show_toolkits:
            console.print(f"Loading toolkit: {loaded_toolkit.name}", style="bold blue")
        catalog.add_toolkit(loaded_toolkit)
    return catalog
