
import os
import toml
import json
import tomlkit

from pathlib import Path
from pydantic import BaseModel, ValidationError, EmailStr, Field
from typing import Dict, List, Optional, TypeVar, Any, Tuple, Union


class PackInfo(BaseModel):
    name: str
    description: str
    version: str
    author: Optional[str]
    email: Optional[EmailStr]


class ToolPack(BaseModel):
    pack: PackInfo
    depends: Optional[Dict[str, str]] = None
    tools: Optional[Dict[str, str]] = {}

    def write_lock_file(self, pack_dir: Union[str, os.PathLike]):
        lock_file = Path(pack_dir) / 'pack.lock.toml'
        pack_dict = self.dict(by_alias=True, exclude_none=True)
        pack_ordered_dict = {
            "pack": pack_dict.get("pack"),
            "depends": pack_dict.get("depends"),
            "tools": pack_dict.get("tools"),
        }

        # Create a tomlkit document from the ordered dictionary
        doc = tomlkit.document()
        for key, value in pack_ordered_dict.items():
            doc[key] = value

        # Write the tomlkit document to file
        with open(lock_file, 'w') as f:
            f.write(tomlkit.dumps(doc))

    @classmethod
    def from_lock_file(cls, pack_dir: Union[str, os.PathLike]):
        pack_dir = Path(pack_dir).resolve()
        lock_file = pack_dir / 'pack.lock.toml'
        with open(lock_file, 'r') as f:
            data = toml.load(f)
        return cls(**data)