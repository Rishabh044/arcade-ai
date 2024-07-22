import ast
from pathlib import Path
from typing import Optional, Union


def load_ast_tree(filepath: str | Path) -> ast.AST:
    """
    Load and parse the Abstract Syntax Tree (AST) from a Python file.

    """
    try:
        with open(filepath) as file:
            return ast.parse(file.read(), filename=filepath)
    except FileNotFoundError:
        raise FileNotFoundError(f"File {filepath} not found")


def get_function_name_if_decorated(
    node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
) -> Optional[str]:
    """
    Check if a function has a decorator
    """
    decorator_ids = {"ar.tool", "tool"}
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id in decorator_ids:
            return node.name
    return None


def get_tools_from_file(filepath: str | Path) -> list[str]:
    """
    Retrieve tools from a Python file.
    """
    tree = load_ast_tree(filepath)
    tools = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            tool_name = get_function_name_if_decorated(node)
            if tool_name:
                tools.append(tool_name)
    return tools
