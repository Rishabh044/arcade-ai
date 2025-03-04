import base64

import typer
from arcadepy import APIConnectionError, APIStatusError, Arcade
from rich.console import Console

from arcade.cli.utils import (
    OrderCommands,
    validate_and_get_config,
)
from arcade.core.cloud import CloudResource

console = Console()


app = typer.Typer(
    cls=OrderCommands,
    add_completion=False,
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_short=True,
)

domains = {
    "prod": {
        "cloud": "https://cloud.arcade.dev",
        "api": "https://api.arcade.dev",
    },
    "dev": {
        "cloud": "https://cloud.bosslevel.dev",
        "api": "https://api.bosslevel.dev",
    },
    "local": {
        "cloud": "http://localhost:8001",
        "api": "http://localhost:9099",
    },
}


@app.command("create", help="Create a new worker")
def create(
    name: str = typer.Argument(..., help="Name of the worker"),
    env: str = typer.Option("dev", "--env", "-e", help="Environment to use"),
) -> None:
    config = validate_and_get_config()

    cloud = CloudResource(url=domains[env]["cloud"], api_key=config.api.key)
    arcade = Arcade(api_key=config.api.key, base_url=domains[env]["api"])

    console.print(f"Starting worker {name}...", style="dim")

    response = cloud.create_worker(name)

    if response.status_code != 200:
        console.print(f"Error creating worker {name}: {response.json()['msg']}", style="red")
        return

    console.print(f"Adding worker {name} to the engine...", style="dim")

    try:
        arcade.worker.create(
            id=name,
            enabled=True,
            http={
                "uri": response.json()["data"]["worker_endpoint"],
                "secret": response.json()["data"]["worker_secret"],
                "timeout": 15,
                "retry": 4,
            },
            timeout=45,
        )
    except APIConnectionError:
        console.print(
            "⚠️ Warning: Arcade Engine was unreachable. (Is it running?)",
            style="bold yellow",
        )
        return
    except APIStatusError:
        console.print(
            f"Error adding worker {name} to the engine: {response.json()["message"]}", style="red"
        )
        return
    console.print("Done.", style="dim")


@app.command("list", help="List all workers")
def list_workers() -> None:
    """List all workers"""
    # Implementation here
    pass


@app.command("rm", help="Delete a worker")
def delete_worker(
    name: str = typer.Argument(..., help="Name of the worker"),
    env: str = typer.Option("dev", "--env", "-e", help="Environment to use"),
) -> None:
    """Delete a worker"""
    config = validate_and_get_config()

    cloud = CloudResource(url=domains[env]["cloud"], api_key=config.api.key)
    arcade = Arcade(api_key=config.api.key, base_url=domains[env]["api"])

    console.print(f"Deleting worker {name}...", style="dim")
    response = cloud.delete_worker(name)
    if response.status_code != 200:
        console.print(f"Failed to delete worker {name}: {response.json()['msg']}", style="red")
        return

    try:
        arcade.worker.delete(name)
    except APIConnectionError:
        console.print(
            "⚠️ Warning: Arcade Engine was unreachable. (Is it running?)",
            style="bold yellow",
        )
        return
    except APIStatusError:
        console.print(
            f"Error deleting worker from engine {name}: {response.json()["message"]}", style="red"
        )
        return
    console.print("Done.", style="dim")


@app.command("add-pkg", help="Add a Python package to a worker from PyPI or local directory")
def add_package(
    worker_name: str = typer.Option(..., "--worker", "-w", help="Name of the worker"),
    package: str = typer.Argument(
        ...,
        help=(
            "Package to install. Can be:\n"
            "- PyPI package (e.g., 'requests>=2.28.0')\n"
            "- Local directory (e.g., './my-package')\n"
            "- Local directory with editable install (e.g., '-e ./my-package')"
        ),
    ),
    env: str = typer.Option("dev", "--env", "-e", help="Environment to use"),
) -> None:
    """
    Add a Python package to a worker's environment. The package can be installed from PyPI
    or from a local directory.

    Examples:
        arcade worker add-package -w my-worker requests>=2.28.0
        arcade worker add-package -w my-worker ./my-local-package
        arcade worker add-package -w my-worker -e ./my-local-package
    """
    import io
    import os
    import tarfile

    config = validate_and_get_config()
    cloud = CloudResource(url=domains[env]["cloud"], api_key=config.api.key)
    arcade = Arcade(api_key=config.api.key, base_url=domains[env]["api"])

    if os.path.exists(package) and os.path.isdir(package):
        if not os.path.isfile(package + "/pyproject.toml") and not os.path.isfile(
            package + "/setup.py"
        ):
            raise typer.BadParameter(f"'{package}' must contain a pyproject.toml or setup.py file")

        console.print(f"Adding local package {package} to worker {worker_name}...", style="dim")
        byte_stream = io.BytesIO()

        # Create a tar archive in memory
        with tarfile.open(fileobj=byte_stream, mode="w:gz") as tar:
            tar.add(package, arcname=os.path.basename(package))

        # Get the byte content
        byte_stream.seek(0)
        b = byte_stream.read()

        package_name = os.path.basename(os.path.normpath(package))

        # Convert bytes to base64 string for JSON serialization
        package_bytes_b64 = base64.b64encode(b).decode("utf-8")

        response = cloud.upload_local_package(worker_name, package_name, package_bytes_b64)

        if response.status_code != 200:
            console.print(
                f"Error adding local package {package} to worker {worker_name}: {response.json()['msg']}",
                style="red",
            )
            return

        if not os.path.isdir(package):
            raise typer.BadParameter(f"'{package}' exists but is not a directory")
    else:
        # If path doesn't exist, assume it's a package name
        console.print(f"Adding PyPI package {package} to worker {worker_name}...", style="dim")
        response = cloud.upload_hosted_package(worker_name, package)
        if response.status_code != 200:
            console.print(
                f"Error adding PyPI package {package} to worker {worker_name}: {response.json()['msg']}",
                style="red",
            )
            return

    try:
        print("Updating worker")
        arcade.worker.update(id=worker_name)
    except APIConnectionError:
        console.print(
            "⚠️ Warning: Arcade Engine was unreachable. (Is it running?)",
            style="bold yellow",
        )
        return

    except APIStatusError as e:
        console.print(f"Error refreshing engine: {e.message}", style="red")
        return

    console.print("Done.", style="dim")


@app.command("rm-pkg", help="Remove a Python package from a worker")
def remove_package(
    worker_name: str = typer.Option(..., "--worker", "-w", help="Name of the worker"),
    package: str = typer.Argument(
        ...,
        help=(
            "Package to install. Can be:\n"
            "- PyPI package (e.g., 'requests>=2.28.0')\n"
            "- Local directory (e.g., './my-package')\n"
            "- Local directory with editable install (e.g., '-e ./my-package')"
        ),
    ),
    env: str = typer.Option("dev", "--env", "-e", help="Environment to use"),
) -> None:
    """
    Remove a Python package from a worker's environment.

    Examples:
        arcade worker remove-package -w my-worker requests
    """
    import os

    config = validate_and_get_config()
    cloud = CloudResource(url=domains[env]["cloud"], api_key=config.api.key)
    arcade = Arcade(api_key=config.api.key, base_url=domains[env]["api"])

    if os.path.exists(package) and os.path.isdir(package):
        package = os.path.basename(os.path.normpath(package))

    console.print(f"Removing package {package} from worker {worker_name}...", style="dim")
    response = cloud.remove_package(worker_name, package)
    if response.status_code != 200:
        console.print(
            f"Error removing package {package} from worker {worker_name}: {response.json()['msg']}",
            style="red",
        )
        return

    try:
        arcade.worker.update(id=worker_name)
    except APIConnectionError:
        console.print(
            "⚠️ Warning: Arcade Engine was unreachable. (Is it running?)",
            style="bold yellow",
        )
        return

    except APIStatusError as e:
        console.print(f"Error refreshing engine: {e.message}", style="red")
        return

    console.print("Done.", style="dim")


def get_package_name(pyproject_path="pyproject.toml"):
    import tomllib

    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)
    return pyproject_data.get("tool", {}).get("poetry", {}).get("name", None)
