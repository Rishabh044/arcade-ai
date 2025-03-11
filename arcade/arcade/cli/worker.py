import httpx
import typer
from arcadepy import Arcade, NotFoundError
from rich.console import Console
from rich.table import Table

from arcade.cli.constants import (
    PROD_CLOUD_HOST,
    PROD_ENGINE_HOST,
)
from arcade.cli.utils import (
    OrderCommands,
    compute_base_url,
    validate_and_get_config,
)

console = Console()


app = typer.Typer(
    cls=OrderCommands,
    add_completion=False,
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_short=True,
)

state = {
    "engine_url": compute_base_url(
        host=PROD_ENGINE_HOST, port=None, force_tls=False, force_no_tls=False
    )
}


@app.callback()
def main(
    host: str = typer.Option(
        PROD_ENGINE_HOST,
        "--host",
        "-h",
        help="The Arcade Engine host.",
    ),
    port: int = typer.Option(
        None,
        "--port",
        "-p",
        help="The port of the Arcade Engine host.",
    ),
    force_tls: bool = typer.Option(
        False,
        "--tls",
        help="Whether to force TLS for the connection to the Arcade Engine.",
    ),
    force_no_tls: bool = typer.Option(
        False,
        "--no-tls",
        help="Whether to disable TLS for the connection to the Arcade Engine.",
    ),
):
    """
    Manage users in the system.
    """
    engine_url = compute_base_url(force_tls, force_no_tls, host, port)
    state["engine_url"] = engine_url


@app.command("list", help="List all workers")
def list_workers() -> None:
    config = validate_and_get_config()
    engine_url = state["engine_url"]
    client = Arcade(api_key=config.api.key, base_url=engine_url)

    print_worker_table(client)


def print_worker_table(client: Arcade) -> None:
    workers = client.workers.list()
    if not workers.items:
        console.print("No workers found", style="bold red")
        return

    # Create and print a table of worker information
    table = Table(title="Workers")
    table.add_column("ID")
    table.add_column("Enabled")
    table.add_column("Host")
    table.add_column("Toolkits")
    for worker in workers.items:
        tools = get_toolkits(client, worker.id)
        table.add_row(
            worker.id,
            str(worker.enabled),
            worker.http.uri if worker.http else "",
            "Cannot get toolkits from disabled workers" if tools == "" else tools,
        )
    console.print(table)


def parse_deployment_response(response: dict) -> None:
    # Check what changes were made to the worker and display
    changes = response["data"]["changes"]
    additions = changes.get("additions", [])
    removals = changes.get("removals", [])
    updates = changes.get("updates", [])
    no_changes = changes.get("no_changes", [])
    print_deployment_table(additions, removals, updates, no_changes)


def print_deployment_table(
    additions: list, removals: list, updates: list, no_changes: list
) -> None:
    table = Table(title="Changed Packages")
    table.add_column("Added", justify="right", style="green")
    table.add_column("Removed", justify="right", style="red")
    table.add_column("Updated", justify="right", style="yellow")
    table.add_column("No Changes", justify="right", style="dim")
    max_rows = max(len(additions), len(removals), len(updates), len(no_changes))

    # Add each row of worker package changes to the table
    for i in range(max_rows):
        addition = additions[i] if i < len(additions) else ""
        removal = removals[i] if i < len(removals) else ""
        update = updates[i] if i < len(updates) else ""
        no_change = no_changes[i] if i < len(no_changes) else ""
        table.add_row(addition, removal, update, no_change)
    console.print(table)


@app.command("enable", help="Enable a worker")
def enable_worker(
    worker_id: str,
) -> None:
    config = validate_and_get_config()
    engine_url = state["engine_url"]
    arcade = Arcade(api_key=config.api.key, base_url=engine_url)
    try:
        arcade.workers.update(worker_id, enabled=True)
    except Exception as e:
        console.print(f"Error enabling worker: {e}", style="bold red")
        raise typer.Exit(code=1)


@app.command("disable", help="Disable a worker")
def disable_worker(
    worker_id: str,
) -> None:
    config = validate_and_get_config()
    engine_url = state["engine_url"]
    arcade = Arcade(api_key=config.api.key, base_url=engine_url)
    try:
        arcade.workers.update(worker_id, enabled=False)
    except Exception as e:
        console.print(f"Error disabling worker: {e}", style="bold red")
        raise typer.Exit(code=1)


@app.command("rm", help="Remove a worker")
def rm_worker(
    worker_id: str,
    cloud_host: str = typer.Option(
        PROD_CLOUD_HOST,
        "--cloud-host",
        "-c",
        help="The Arcade Engine host.",
    ),
    cloud_port: int = typer.Option(
        None,
        "--cloud-port",
        "-cp",
        help="The port of the Arcade Engine host.",
    ),
    force_tls: bool = typer.Option(
        False,
        "--tls",
        help="Whether to force TLS for the connection to the Arcade Engine.",
    ),
    force_no_tls: bool = typer.Option(
        False,
        "--no-tls",
        help="Whether to disable TLS for the connection to the Arcade Engine.",
    ),
) -> None:
    config = validate_and_get_config()
    engine_url = state["engine_url"]
    cloud_url = compute_base_url(force_tls, force_no_tls, cloud_host, cloud_port)

    # First attempt to delete from the cloud
    try:
        client = httpx.Client()
        response = client.delete(
            f"{cloud_url}/api/v1/workers/{worker_id}",
            headers={"Authorization": f"Bearer {config.api.key}"},
        )
        response.raise_for_status()
    except Exception as e:
        console.print(f"Error deleting deployment: {e}", style="bold red")
        raise typer.Exit(code=1)

    # Then try to delete from the engine
    try:
        arcade = Arcade(api_key=config.api.key, base_url=engine_url)
        arcade.workers.delete(worker_id)
    except Exception as e:
        console.print(f"Error deleting worker from engine: {e}", style="bold red")
        raise typer.Exit(code=1)


def get_toolkits(client: Arcade, worker_id: str) -> list[str]:
    try:
        tools = client.workers.tools(worker_id)
        toolkits: list[str] = []
        for tool in tools.items:
            if tool.toolkit.name not in toolkits:
                toolkits.append(tool.toolkit.name)
        return ", ".join(toolkits)
    except NotFoundError:
        return ""
    except Exception as e:
        console.print(f"Error getting worker tools: {e}", style="bold red")
        raise typer.Exit(code=1)
