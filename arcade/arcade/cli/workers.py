import base64

import requests
import typer
from rich.console import Console

from arcade.cli.utils import (
    OrderCommands,
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


@app.command("create", help="Create a new worker")
def create(
    name: str = typer.Argument(..., help="Name of the worker"),
) -> None:
    config = validate_and_get_config()

    console.print(f"Starting worker {name}...", style="dim")
    response = requests.post(
        "http://localhost:8001/api/v1/workers",
        headers={"Authorization": f"Bearer {config.api.key}"},
        json={"name": name},
        timeout=45,
    )
    if response.status_code != 200:
        console.print(f"Error creating worker {name}: {response.json()['msg']}", style="red")
        return

    console.print(f"Adding worker {name} to the engine...", style="dim")

    response = requests.post(
        "http://localhost:9099/v1/admin/workers",
        headers={"Authorization": f"Bearer {config.api.key}"},
        json={
            "id": name,
            "enabled": True,
            "http": {
                "uri": response.json()["data"]["worker_endpoint"],
                "secret": response.json()["data"]["worker_secret"],
                "timeout": 1,
                "retry": 4,
            },
        },
        timeout=45,
    )
    if response.status_code != 200:
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


@app.command("delete", help="Delete a worker")
def delete_worker(name: str = typer.Argument(..., help="Name of the worker")) -> None:
    """Delete a worker"""
    config = validate_and_get_config()
    console.print(f"Deleting worker {name}...", style="dim")
    response = requests.delete(
        f"http://localhost:8001/api/v1/workers/{name}",
        headers={"Authorization": f"Bearer {config.api.key}"},
        timeout=45,
    )
    if response.status_code != 200:
        console.print(f"Error deleting worker {name}: {response.json()['msg']}", style="red")
        return

    response = requests.delete(
        f"http://localhost:9099/v1/admin/workers/{name}",
        headers={"Authorization": f"Bearer {config.api.key}"},
        timeout=45,
    )
    if response.status_code != 204:
        console.print(
            f"Error deleting worker from engine {name}: {response.json()["message"]}", style="red"
        )
        return
    console.print("Done.", style="dim")


@app.command("add-package", help="Add a Python package to a worker from PyPI or local directory")
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
    # index_url: str = typer.Option(
    #     None,
    #     "--index",
    #     "-i",
    #     help="Alternative Python package index URL"
    # ),
    # extra_index_url: str = typer.Option(
    #     None,
    #     "--extra-index",
    #     "-e",
    #     help="Additional Python package index URL"
    # ),
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

    if os.path.exists(package):
        if os.path.isdir(package):
            console.print(f"Adding local package {package} to worker {worker_name}...", style="dim")
            # return os.path.abspath(package)  # Return absolute path if it's a directory
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

            config = validate_and_get_config()
            response = requests.patch(
                "http://localhost:8001/api/v1/workers/add_local_package",
                headers={"Authorization": f"Bearer {config.api.key}"},
                json={
                    "worker_name": worker_name,
                    "package_name": package_name,
                    "package_bytes": package_bytes_b64,  # Send base64 encoded string
                },
                timeout=120,
            )
            if response.status_code != 200:
                console.print(
                    f"Error adding local package {package} to worker {worker_name}: {response.json()['msg']}",
                    style="red",
                )
                return

        else:
            raise typer.BadParameter(f"'{package}' exists but is not a directory")
    else:
        # If path doesn't exist, assume it's a package name
        console.print(f"Adding PyPI package {package} to worker {worker_name}...", style="dim")
        config = validate_and_get_config()
        response = requests.patch(
            "http://localhost:8001/api/v1/workers/add_package",
            headers={"Authorization": f"Bearer {config.api.key}"},
            json={"worker_name": worker_name, "package_name": package},
            timeout=45,
        )
        if response.status_code != 200:
            console.print(
                f"Error adding PyPI package {package} to worker {worker_name}: {response.json()['msg']}",
                style="red",
            )
            return

    console.print("Done.", style="dim")


@app.command("remove-package", help="Remove a Python package from a worker")
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
) -> None:
    """
    Remove a Python package from a worker's environment.

    Examples:
        arcade worker remove-package -w my-worker requests
    """
    config = validate_and_get_config()
    console.print(f"Removing package {package} from worker {worker_name}...", style="dim")
    response = requests.patch(
        "http://localhost:8001/api/v1/workers/remove_package",
        headers={"Authorization": f"Bearer {config.api.key}"},
        json={"worker_name": worker_name, "package_name": package},
        timeout=45,
    )
    if response.status_code != 200:
        console.print(
            f"Error removing package {package} from worker {worker_name}: {response.json()['msg']}",
            style="red",
        )
        return

    console.print("Done.", style="dim")


def get_package_name(pyproject_path="pyproject.toml"):
    import tomllib

    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)
    return pyproject_data.get("tool", {}).get("poetry", {}).get("name", None)
