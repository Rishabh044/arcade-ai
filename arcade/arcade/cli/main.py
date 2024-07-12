import json
import os

import requests
import typer
import uvicorn
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from arcade.actor.core.conf import settings

cli = typer.Typer()
console = Console()


@cli.command(help="Start an Actor serving tools over HTTP.")
def serve(
    host: str = typer.Option(
        settings.UVICORN_HOST,
        help="Host for the app, from settings by default.",
        show_default=True,
    ),
    port: int = typer.Option(
        settings.UVICORN_PORT,
        help="Port for the app, settings default.",
        show_default=True,
    ),
):
    """
    Starts the actor with host, port, and reload options. Uses
    Uvicorn as ASGI actor. Parameters allow runtime configuration.
    """
    from arcade.actor.main import app

    try:
        uvicorn.run(
            app=app,
            host=host,
            port=port,
        )
    except KeyboardInterrupt:
        console.print("actor stopped by user.", style="bold red")
        typer.Exit()
    except Exception as e:
        error_message = f"❌ Failed to start Toolserver: {escape(str(e))}"
        console.print(error_message, style="bold red")
        raise typer.Exit(code=1)


@cli.command(help="Build a new Tool Pack")
def pack(
    directory: str = typer.Option(os.getcwd(), "--dir", help="tools directory path with pack.toml"),
):
    """
    Creates a new tool pack with the given name, description, and result type.
    """
    from arcade.apm.pack import Packer

    try:
        pack = Packer(directory)
        pack.create_pack()
    except Exception as e:
        error_message = f"❌ Failed to build Tool Pack: {escape(str(e))}"
        console.print(error_message, style="bold red")
        raise typer.Exit(code=1)


@cli.command(help="Show out the available tools")
def show(
    directory: str = typer.Option(None, "--dir", help="tools directory path with pack.toml"),
    actor: str = typer.Option("http://localhost:8000", help="The actor to use for prediction."),
):
    """
    Creates a new tool pack with the given name, description, and result type.
    """

    from arcade.tool.catalog import ToolCatalog

    try:
        if directory:
            # Initialize ToolCatalog with the specified directory
            catalog = ToolCatalog(directory)
            tools = catalog.list_tools()
        else:
            # handle this better
            # Call the /v1/tool/list_tools route
            response = requests.get(f"{actor}/v1/tools/list")
            tools = json.loads(response.text)["data"]

        # Create a table with Rich library
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name")
        table.add_column("Version")
        table.add_column("Description")

        for tool in tools:
            table.add_row(tool["name"], tool["version"], tool["description"])

        console.print(table)

    except Exception as e:
        # better erorr message here
        error_message = f"❌ Failed to List tools: {escape(str(e))}"
        console.print(error_message, style="bold red")
        raise typer.Exit(code=1)


@cli.command(help="Run a tool using an LLM to predict the arguments")
def run(
    tool: str = typer.Argument(..., help="The name of the tool to run."),
    prompt: str = typer.Option(..., "-p", "--prompt", help="The prompt to use for prediction."),
    model: str = typer.Option("gpt-3.5-turbo", help="The model to use for prediction."),
    actor: str = typer.Option("http://localhost:8000", help="The actor to use for prediction."),
):
    """
    Run a tool using an LLM to predict the arguments.
    """
    pass


@cli.command(help="Execute eval suite wthin /evals")
def evals(
    module: str = typer.Option(..., help="The name of the module to run evals on"),
):
    """
    Execute eval suite wthin /evals
    """
    pass


@cli.command(help="Create a new Tool Pack directory")
def new(
    directory: str = typer.Option(os.getcwd(), "--dir", help="tools directory path with pack.toml"),
):
    """
    Creates a new tool pack with the given name, description, and result type.
    """
    from arcade.apm.new import create_new_pack

    try:
        create_new_pack(directory)
    except Exception as e:
        error_message = f"❌ Failed to create new Tool Pack: {escape(str(e))}"
        console.print(error_message, style="bold red")
        raise typer.Exit(code=1)


@cli.command(help="Deploy the actor to a serverless cloud service")
def deploy(
    modal: bool = typer.Option(False, "--modal", help="Deploy this actor as a Modal app"),
    aws: bool = typer.Option(False, "--aws", help="Build this actor as an AWS Lambda"),
    gcp: bool = typer.Option(False, "--gcp", help="Build this actor as a Google Cloud Function"),
    azure: bool = typer.Option(False, "--azure", help="Build this actor as an Azure Function"),
    docker: bool = typer.Option(False, "--docker", help="Deploy this actor as a Docker container"),
):
    """
    Deploy the actor to the cloud.
    """
    pass


@cli.command(help="Build the actor into a distributable package")
def build(
    docker: bool = typer.Option(False, "--docker", help="Build this actor as a Docker container"),
):
    pass


@cli.command(help="Log in to Arcade Cloud")
def login(
    username: str = typer.Option(..., prompt="Username", help="Your Arcade Cloud username"),
    api_key: str = typer.Option(..., prompt="API Key", help="Your Arcade Cloud API Key"),
):
    """
    Logs the user into Arcade Cloud.
    """
    # Here you would add the logic to authenticate the user with Arcade Cloud
    pass
