import itertools
from pathlib import Path

import toml

from arcade.sdk import ToolCatalog, Toolkit

"""
Assumes the toolkit is in your current environment. i.e., you have run `pip install -e .` from the root directory of the toolkit.
"""


def snake_to_camel(snake_str):
    """Convert a snake_case string to a CamelCase string."""
    components = snake_str.split("_")
    return "".join(component.capitalize() for component in components)


readme = ""

# Read the package name from pyproject.toml
pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
with pyproject_path.open() as pyproject_file:
    pyproject_data = toml.load(pyproject_file)
    package_name = pyproject_data["tool"]["poetry"]["name"]

toolkit = Toolkit.from_package(package_name)

# Extracting information from the toolkit
name = toolkit.name
version = toolkit.version
description = toolkit.description
author = ", ".join(toolkit.author)
repository = toolkit.repository
file_path_to_tool_names = {
    file: tools for file, tools in toolkit.tools.items() if tools
}  # tool names are snake_case here
tool_names = list(
    itertools.chain.from_iterable(file_path_to_tool_names.values())
)  # tool names are snake_case here

# Title
readme += f"# {name.capitalize()} Toolkit\n\n"

# Metadata table about the toolkit
toolkit_metadata_table = f"""
|             |                                                                         |
|-------------|-------------------------------------------------------------------------|
| Name        | {name}                                                                  |
| Package     | {package_name}                                                          |
| Version     | {version}                                                               |
| Description | {description}                                                           |
| Author      | {author}                                                                |
"""

readme += toolkit_metadata_table

# Tool TOC
catalog = ToolCatalog()
catalog.add_toolkit(toolkit)
tools = [t.definition for t in list(catalog)]
tool_name_to_description = {tool.name: tool.description for tool in tools}

tool_toc_table = """
| Tool Name   | Description                                                             |
|-------------|-------------------------------------------------------------------------|
"""

for tool_name, description in tool_name_to_description.items():
    description_preview = description.split("\n")[0]
    tool_toc_table += f"| {tool_name} | {description_preview} |\n"

readme += tool_toc_table

# Detail each tool
tool_name_to_inputs = {tool.name: tool.inputs for tool in tools}
for file_path, tool_names in file_path_to_tool_names.items():
    tool_section = f"\n## {file_path.split('.')[-1].capitalize()}\n\n"
    for tool_name in tool_names:
        tool_name_camel = snake_to_camel(tool_name)
        tool_section += f"### {tool_name_camel}\n\n"
        tool_section += tool_name_to_description[tool_name_camel] + "\n\n"
        inputs = tool_name_to_inputs[tool_name_camel]
        parameters = inputs.parameters
        if not parameters:
            continue
        tool_section += "#### Parameters\n\n"
        for parameter in parameters:
            enum_values = ""
            if parameter.value_schema.enum:
                enum_values = ", ".join(f"'{value}'" for value in parameter.value_schema.enum)

            name = parameter.name
            param_type = parameter.value_schema.val_type
            required = "required" if parameter.required else "optional"
            description = parameter.description or ""
            tool_section += f"- `{name}` *({param_type}, {required})* {description}"
            if enum_values:
                tool_section += f", Valid values are {enum_values}"
            tool_section += "\n\n"

    readme += tool_section

readme_path = Path(__file__).parent.parent / "README.md"
with readme_path.open("w") as file:
    file.write(readme)
