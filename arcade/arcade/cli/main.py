import os

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table
from typer.core import TyperGroup
from typer.models import Context


class OrderCommands(TyperGroup):
    def list_commands(self, ctx: Context):
        """Return list of commands in the order appear."""
        return list(self.commands)  # get commands using self.commands


console = Console()
cli = typer.Typer(
    cls=OrderCommands,
)


@cli.command(help="Log in to Arcade Cloud")
def login(
    username: str = typer.Option(..., prompt="Username", help="Your Arcade Cloud username"),
    api_key: str = typer.Option(None, prompt="API Key", help="Your Arcade Cloud API Key"),
):
    """
    Logs the user into Arcade Cloud.
    """
    # Here you would add the logic to authenticate the user with Arcade Cloud
    pass


@cli.command(help="Create a new toolkit package directory")
def new(
    directory: str = typer.Option(os.getcwd(), "--dir", help="tools directory path"),
):
    """
    Creates a new toolkit with the given name, description, and result type.
    """
    from arcade.cli.new import create_new_toolkit

    try:
        create_new_toolkit(directory)
    except Exception as e:
        error_message = f"❌ Failed to create new Toolkit: {escape(str(e))}"
        console.print(error_message, style="bold red")
        raise typer.Exit(code=1)


@cli.command(help="Show the available tools in an actor or toolkit directory")
def show(
    directory: str = typer.Option(os.getcwd(), "--dir", help="toolkit directory path"),
    actor: str = typer.Option("http://localhost:8000", help="The actor to use for prediction."),
):
    """
    Creates a new tool pack with the given name, description, and result type.
    """

    from arcade.core.catalog import ToolCatalog
    from arcade.core.toolkit import Toolkit

    try:
        if directory:
            # Initialize ToolCatalog with the specified directory
            toolkit = Toolkit.from_directory(directory)
            catalog = ToolCatalog()
            catalog.add_toolkit(toolkit)
        else:
            # handle this better
            # Call the /v1/tool/list_tools route
            typer.exit("❌ Directory not specified")

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
        error_message = f"❌ Failed to List tools: {escape(e)}"
        console.print(error_message, style="bold red")
        raise typer.Exit(code=1)


@cli.command(help="Run a tool using an LLM to predict the arguments")
def run(
    prompt: str = typer.Argument(..., help="The prompt to use for context"),
    model: str = typer.Option("gpt-3.5-turbo", "-m", help="The model to use for prediction."),
    tool: str = typer.Option(None, "-t", "--tool", help="The name of the tool to run."),
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


@cli.command(help="Manage the Arcade Engine (start/stop/restart)")
def engine(
    action: str = typer.Argument("start", help="The action to take (start/stop/restart)"),
    host: str = typer.Option("localhost", "--host", "-h", help="The host of the engine"),
    port: int = typer.Option(6901, "--port", "-p", help="The port of the engine"),
):
    """
    Manage the Arcade Engine (start/stop/restart)
    """
    pass


@cli.command(help="Manage credientials stored in the Arcade Engine")
def credentials(
    action: str = typer.Argument("show", help="The action to take (add/remove/show)"),
    name: str = typer.Option(None, "--name", "-n", help="The name of the credential to add/remove"),
    val: str = typer.Option(None, "--val", "-v", help="The value of the credential to add/remove"),
):
    """
    Manage credientials stored in the Arcade Engine
    """
    pass


@cli.command(help="Show/edit configuration details of the Arcade Engine")
def config(
    action: str = typer.Argument("show", help="The action to take (show/edit)"),
    name: str = typer.Option(None, "--name", "-n", help="The name of the configuration to edit"),
    val: str = typer.Option(None, "--val", "-v", help="The value of the configuration to edit"),
):
    """
    Show/edit configuration details of the Arcade Engine
    """
    pass
