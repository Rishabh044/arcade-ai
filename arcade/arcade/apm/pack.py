import os
import shutil
from pathlib import Path
from typing import Union

import toml
from pydantic import ValidationError

from arcade.apm.base import PackInfo, ToolPack
from arcade.apm.parse import get_tools_from_file
from arcade.utils import snake_to_pascal_case


class Packer:
    def __init__(self, pack_dir: Union[str, os.PathLike]):
        self.pack_dir = Path(pack_dir).resolve()
        self.tools_dir = self.pack_dir / "tools"
        # Load the action pack configuration from a TOML file
        try:
            with open(self.pack_dir / "pack.toml") as f:
                pack_data = toml.load(f)

            self.pack = PackInfo(**pack_data["pack"])
            self.modules = pack_data["modules"]

        except FileNotFoundError:
            raise FileNotFoundError(f"No 'pack.toml' found in {self.tools_dir}")
        except (toml.TomlDecodeError, ValidationError) as e:
            raise ValueError(f"Invalid 'pack.toml' format: {e}")

        self.tools = self.load_tools()
        self.depends = {}  # TODO
        self.packs = []  # TODO

    def load_tools(self) -> dict[str, str]:
        tools = {}
        for tool_file in self.tools_dir.rglob("*.py"):
            if "__init__.py" in tool_file.name:
                continue
            try:
                module = tool_file.stem
                version = self.modules.get(module, "latest")

                found_tools = get_tools_from_file(tool_file)
                for tool in found_tools:
                    tool_name = module + "." + tool + "@" + version
                    tools[snake_to_pascal_case(tool)] = tool_name
            except Exception as e:
                print(f"Error loading tool from {tool_file}: {e}")
        return tools

    def _create_pack_dir(self, pack: ToolPack) -> Path:
        # Make "packs" directory if it doesn't exist
        packs_dir = self.pack_dir / "packs"
        os.makedirs(packs_dir, exist_ok=True)
        # make the dir for the action pack and the version (making parent dirs if needed)
        top_pack_dir = packs_dir / pack.pack.name / pack.pack.version
        # If the pack already exists, remove it and recreate it
        if top_pack_dir.exists():
            shutil.rmtree(top_pack_dir)
        os.makedirs(top_pack_dir, exist_ok=True)
        return top_pack_dir

    def create_pack(self):
        # Create an ActionPack instance from the loaded data
        pack = ToolPack(pack=self.pack, depends=self.depends, tools=self.tools)
        # pack_dir = self._create_pack_dir(pack)
        # Write the action pack to a TOML file
        pack.write_lock_file(self.pack_dir)
