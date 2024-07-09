import ast
import importlib.metadata
import importlib.util
import sys
from typing import Optional

from stdlib_list import stdlib_list


def load_ast_tree(filepath: str) -> ast.AST:
    """
    Load and parse the Abstract Syntax Tree (AST) from a Python file.

    :param filepath: Path to the Python file.
    :return: AST of the Python file.
    """
    try:
        with open(filepath) as file:
            return ast.parse(file.read(), filename=filepath)
    except FileNotFoundError:
        raise FileNotFoundError(f"File {filepath} not found")


def get_python_version() -> str:
    """
    Get the current Python version.

    :return: The version of Python in use.
    """
    return f"{sys.version_info.major}.{sys.version_info.minor}"


def retrieve_imported_libraries(tree: ast.AST) -> dict[str, Optional[str]]:
    """
    Retrieve non-standard libraries imported in the AST.

    :param tree: The AST of the file.
    :return: A dictionary with libraries as keys and their versions as values.
    """
    libraries = {}
    python_version = get_python_version()
    stdlib_modules = stdlib_list(python_version)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            package_name = node.module.split(".")[0] if node.module else None
            if package_name == "dstar" or package_name in stdlib_modules:
                continue
            try:
                package_version = importlib.metadata.version(package_name)
            except importlib.metadata.PackageNotFoundError:
                package_version = None
            libraries[package_name] = package_version
    return libraries


def get_function_name_if_decorated(node: ast.FunctionDef) -> Optional[str]:
    """
    Check if a function has a decorator of either "@toolserve.tool" or "tool" and return the function's name.

    :param node: The function definition node from the AST.
    :return: The name of the function if it has the specified decorators, otherwise None.
    """
    decorator_ids = {"toolserve.tool", "tool"}
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id in decorator_ids:
            return node.name
    return None


def get_tools_from_file(filepath: str) -> list[str]:
    """
    Get the names of all functions in a Python file that are decorated with either "@toolserve.tool" or "@tool".

    :param filepath: Path to the Python file.
    :return: List of function names.
    """
    tree = load_ast_tree(filepath)
    tools = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            tool_name = get_function_name_if_decorated(node)
            if tool_name:
                tools.append(tool_name)
    return tools
