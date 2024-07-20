from collections import defaultdict
from pathlib import Path
from typing import Any, Union

import toml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from arcade.core.parse import get_tools_from_file


class Toolkit(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(alias="tool.poetry.name")
    package_name: str = Field(alias="tool.poetry.name")
    version: str = Field(alias="tool.poetry.version")
    description: str = Field(alias="tool.poetry.description")
    author: list[str] = Field(alias="tool.poetry.authors")
    dependencies: dict[str, str] = Field(alias="tool.poetry.dependencies")
    tools: dict[str, list[str]] = defaultdict(list)

    @model_validator(mode="before")
    def strip_arcade_prefix(cls, values: dict[str, Any]) -> dict[str, Any]:
        name = values.get("tool", {}).get("poetry", {}).get("name")
        if name and name.startswith("arcade_"):
            values["tool"]["poetry"]["name"] = name[7:]
        return values

    @classmethod
    def from_directory(cls, directory: Union[str, Path]) -> "Toolkit":
        directory = Path(directory)
        pyproject_path = directory / "pyproject.toml"

        if not pyproject_path.exists():
            raise FileNotFoundError(f"No 'pyproject.toml' found in {directory}")

        # TODO Error handling
        with open(pyproject_path) as f:
            data = toml.load(f)

        # TODO: handle other PM types

        # poetry
        if "tool" not in data:
            raise ValueError("No 'tool' section found in 'pyproject.toml'")

        poetry = data["tool"].get("poetry", None)
        if not poetry:
            raise ValueError("No 'tool.poetry' section found in 'pyproject.toml'")

        toolkit = Toolkit(
            name=poetry.get("name"),
            package_name=poetry.get("name"),
            version=poetry.get("version"),
            description=poetry.get("description"),
            author=poetry.get("authors"),
            # TODO: also get dev-dependencies?
            dependencies=poetry.get("dependencies"),
        )

        if "arcade" not in data["tool"]:
            raise ValueError("No 'tool.arcade' section found in 'pyproject.toml'")
        modules = data["tool"]["arcade"].get("modules", [])

        if not modules:
            raise ValueError("No 'tool.arcade.modules' found in 'pyproject.toml'")

        for module in modules:
            module_path = directory / f"{module.replace('.', '/')}.py"
            toolkit.tools[module] = get_tools_from_file(module_path)

        return toolkit
