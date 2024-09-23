import inspect
import sys
from pathlib import Path
from typing import List

from arcade.core.catalog import ToolCatalog
from arcade.core.toolkit import Toolkit
from arcade.core.schema import InputParameter

# Assuming 'toolkits' directory is in the parent directory of this script
BASE_DIR = Path(__file__).resolve().parent.parent
TOOLKITS_DIR = BASE_DIR / "toolkits"
OUTPUT_DIR = BASE_DIR / "toolhub"


def main():
    # Ensure the output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize the tool catalog
    catalog = ToolCatalog()

    # Collect all toolkits
    toolkits = []
    for toolkit_dir in TOOLKITS_DIR.iterdir():
        if toolkit_dir.is_dir() and not toolkit_dir.name.startswith("__"):
            for sub_dir in toolkit_dir.iterdir():
                if sub_dir.is_dir() and sub_dir.name.startswith("arcade_"):
                    try:
                        # Add the subdirectory's path to sys.path to import it
                        sys.path.insert(0, str(sub_dir))

                        # Import the toolkit module
                        toolkit_name = sub_dir.name
                        toolkit_package = toolkit_name.replace("-", "_")
                        toolkit_module = __import__(toolkit_package)

                        # Load the toolkit using Arcade's Toolkit class
                        toolkit = Toolkit.from_module(toolkit_module)

                        # Add tools from the toolkit to the catalog
                        catalog.add_toolkit(toolkit)

                        toolkits.append(toolkit)
                    except Exception as e:
                        print(f"Failed to load toolkit {sub_dir.name}: {e}")
                    finally:
                        sys.path.pop(0)

    # Generate documentation for each toolkit
    for toolkit in toolkits:
        # Convert tool names to capitalized camel case
        toolkit.tools = {
            module_name: [to_camel_case(tool_name) for tool_name in tool_names]
            for module_name, tool_names in toolkit.tools.items()
        }
        generate_toolkit_docs(toolkit, catalog)
        generate_toolkit_index(toolkit)

    # Generate index.mdx
    generate_index_mdx(toolkits)


def generate_toolkit_docs(toolkit: Toolkit, catalog: ToolCatalog):
    # Create a subdirectory for the toolkit
    toolkit_dir = OUTPUT_DIR / toolkit.name
    toolkit_dir.mkdir(parents=True, exist_ok=True)

    for module_name, tool_names in toolkit.tools.items():
        if not tool_names:
            continue  # Skip modules without tools

        # Create an .mdx file for each module
        module_name_without_package = module_name.split(".")[-1]
        module_mdx = toolkit_dir / f"{module_name_without_package}.mdx"
        with open(module_mdx, "w", encoding="utf-8") as f:
            f.write(
                f"# {toolkit.name.capitalize()} {module_name_without_package.capitalize()} Tools\n\n"
            )
            f.write(
                f"**Description:** Tools for {module_name_without_package} in the {toolkit.name.capitalize()} toolkit\n\n"
            )

            # Write tools in this module
            for tool_name in tool_names:
                try:
                    module = __import__(module_name, fromlist=[tool_name])
                    tool_func = getattr(module, to_snake_case(tool_name))
                    # Retrieve the tool definition from the catalog
                    materialized_tool = catalog.tools.get(tool_name)
                    if not materialized_tool:
                        continue  # Skip if tool not found in catalog
                    tool_def = materialized_tool.definition

                    # Get the function signature
                    sig = inspect.signature(tool_func)
                    params_sig = sig.parameters

                    # Map parameter names to default values
                    param_defaults = {}
                    for name, param_sig in params_sig.items():
                        default = param_sig.default
                        if default is not inspect.Parameter.empty:
                            param_defaults[name] = default

                    f.write(f"## {tool_def.name}\n\n")
                    f.write(f"{tool_def.description}\n\n")
                    f.write("### **Parameters:**\n\n")
                    if tool_def.inputs.parameters:
                        for i, param in enumerate(tool_def.inputs.parameters):
                            param_name = param.name
                            param_type = get_param_type(param)
                            param_type = (
                                '<span className="tool-param-type">'
                                + param_type
                                + "</span>"
                            )
                            param_description = param.description or ""
                            required_text = (
                                '<span className="tool-param-required">Required</span>'
                                if param.required
                                else '<span className="tool-param-optional">Optional</span>'
                            )
                            default_text = (
                                '<span className="tool-param-default">'
                                + f"Defaults to {param_defaults[param_name]}"
                                + "</span>"
                                if param_name in param_defaults
                                else ""
                            )
                            f.write(
                                f"**{param_name}**&nbsp;&nbsp;&nbsp;{param_type}&nbsp;&nbsp;&nbsp;{required_text}&nbsp;&nbsp;&nbsp;{default_text}  \n"
                            )
                            f.write(f"{param_description}\n")
                            if i < len(tool_def.inputs.parameters) - 1:
                                f.write(
                                    "<hr style={{borderTop: '0.5px solid #888', margin: '10px 0'}} />\n"
                                )
                    else:
                        f.write("This tool does not accept any parameters.\n")
                    f.write("\n---\n\n")
                except Exception as e:
                    print(f"Failed to document tool {tool_name} in {module_name}: {e}")


def generate_toolkit_index(toolkit: Toolkit):
    toolkit_mdx = OUTPUT_DIR / f"{toolkit.name}.mdx"
    with open(toolkit_mdx, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(f"title: {toolkit.name.capitalize()} Toolkit\n")
        f.write(f"description: {toolkit.description}\n")
        f.write("---\n\n")
        for module_name, tool_names in toolkit.tools.items():
            if not tool_names:
                continue  # Skip modules without tools
            module_name_without_package = module_name.split(".")[-1]
            module_link = f"./{toolkit.name}/{module_name_without_package}.mdx"
            f.write(
                f"### [{module_name_without_package.capitalize()}]({module_link})\n\n"
            )
            for tool_name in tool_names:
                tool_link = f"{module_link}#{tool_name.lower()}"
                f.write(f"- [{tool_name}]({tool_link})\n")
        f.write("\n---\n\n")


def to_camel_case(snake_str: str) -> str:
    components = snake_str.split("_")
    return "".join(x.title() for x in components)


def to_snake_case(camel_str: str) -> str:
    import re

    return re.sub(r"(?<!^)(?=[A-Z])", "_", camel_str).lower()


def get_param_type(param: InputParameter) -> str:
    if param.value_schema:
        return param.value_schema.val_type or "Unknown"
    return "Unknown"


def generate_index_mdx(toolkits: List[Toolkit]):
    index_mdx = OUTPUT_DIR / "index.mdx"
    with open(index_mdx, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write("title: ToolHub\n")
        f.write(
            "description: Registry of all tools available in the Arcade AI ecosystem\n"
        )
        f.write("---\n\n")
        f.write("# Tool Registry\n\n")
        f.write(
            "The Arcade AI Tool Registry is a collection of tools that are organized into toolkits that are available to use in the Arcade AI ecosystem.\n\n"
        )
        for toolkit in toolkits:
            f.write(
                f"## [{toolkit.name.capitalize()} Toolkit](./toolhub/{toolkit.name}.mdx)\n\n"
            )
            f.write(f"{toolkit.description}\n\n")
            for module_name, tool_names in toolkit.tools.items():
                if not tool_names:
                    continue  # Skip modules without tools
                module_name_without_package = module_name.split(".")[-1]
                module_link = (
                    f"./toolhub/{toolkit.name}/{module_name_without_package}.mdx"
                )
                f.write(
                    f"### [{module_name_without_package.capitalize()}]({module_link})\n\n"
                )
                for tool_name in tool_names:
                    tool_link = f"{module_link}#{tool_name.lower()}"
                    f.write(f"- [{tool_name}]({tool_link})\n")
            f.write("\n---\n\n")


if __name__ == "__main__":
    main()
