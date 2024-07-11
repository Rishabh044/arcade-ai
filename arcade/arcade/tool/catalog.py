import inspect
import sys
from datetime import datetime
from importlib import import_module
from pathlib import Path
from typing import (
    Annotated,
    Callable,
    Literal,
    Optional,
    Union,
    get_args,
    get_origin,
)

from pydantic import BaseModel, Field, create_model

from arcade.actor.common.response import ResponseModel
from arcade.actor.common.response_code import CustomResponseCode
from arcade.actor.core.conf import settings
from arcade.apm.base import ToolPack
from arcade.sdk.annotations import Inferrable
from arcade.sdk.models import (
    InputParameter,
    ToolDefinition,
    ToolInputs,
    ToolOutput,
    ToolRequirements,
    ValueSchema,
)
from arcade.utils import snake_to_camel


class ToolMeta(BaseModel):
    module: str
    path: str
    date_added: datetime = Field(default_factory=datetime.now)
    date_updated: datetime = Field(default_factory=datetime.now)


class MaterializedTool(BaseModel):
    tool: Callable
    definition: ToolDefinition
    meta: ToolMeta


class ToolCatalog:
    def __init__(self, tools_dir: str = settings.TOOLS_DIR):
        self.tools = self.read_tools(tools_dir)

    @staticmethod
    def read_tools(directory: str) -> list[ToolDefinition]:
        toolpack = ToolPack.from_lock_file(directory)
        sys.path.append(str(Path(directory).resolve() / "tools"))

        tools = {}
        for name, tool_spec in toolpack.tools.items():
            print(name, tool_spec)
            module_name, versioned_tool = tool_spec.split(".", 1)
            func_name, version = versioned_tool.split("@")

            module = import_module(module_name)
            tool_func = getattr(module, func_name)
            tools[name] = MaterializedTool(
                definition=ToolCatalog.create_tool_definition(tool_func, version),
                tool=tool_func,
                meta=ToolMeta(module=module_name, path=module.__file__),
            )

        return tools

    @staticmethod
    def create_tool_definition(tool: Callable, version: str) -> ToolDefinition:
        tool_name = getattr(tool, "__tool_name__", tool.__name__)
        tool_description = getattr(tool, "__tool_description__", None)
        if tool_description is None:
            tool_description = tool.__doc__ or "No description provided."

        tool_def = ToolDefinition(
            name=tool_name,
            description=tool_description,
            version=version,
            inputs=create_input_model(tool),
            output=create_output_model(tool),
            requirements=ToolRequirements(
                authorization=getattr(tool, "__tool_requires_auth__", None),
            ),
        )
        return tool_def

    def __getitem__(self, name: str) -> Optional[ToolDefinition]:
        # TODO error handling
        for tool_name, tool in self.tools.items():
            if tool_name == name:
                return tool
        return None

    def get_tool(self, name: str) -> Optional[Callable]:
        for tool in self.tools:
            if tool.name == name:
                return tool.tool
        return None

    def list_tools(self) -> list[dict[str, str]]:
        def get_tool_endpoint(t: ToolDefinition) -> str:
            return f"/tool/{t.meta.module}/{t.name}"

        return [
            {
                "name": t.name,
                "description": t.description,
                "endpoint": get_tool_endpoint(t),
            }
            for t in self.tools.values()
        ]


def create_input_model(func: Callable) -> ToolInputs:
    """
    Create an input model for a function based on its parameters.
    """
    input_parameters = []
    for name, param in inspect.signature(func, follow_wrapped=True).parameters.items():
        field_info = extract_field_info(param)

        is_enum = False
        enum_values = []

        # Special case: Literal["string1", "string2"] can be enumerated on the wire
        if is_string_literal(field_info["field_params"]["type"]):
            is_enum = True
            enum_values = get_args(field_info["field_params"]["type"])

        input_parameters.append(
            InputParameter(
                name=name,
                description=field_info["field_params"]["description"],
                required=field_info["field_params"]["default"] is None
                and not field_info["field_params"]["optional"],
                inferrable=field_info["field_params"]["inferrable"],
                value_schema=ValueSchema(
                    val_type=field_info["field_params"]["wire_type"],
                    enum=enum_values if is_enum else None,
                ),
            )
        )

    return ToolInputs(parameters=input_parameters)


def is_string_literal(_type: type) -> bool:
    return get_origin(_type) is Literal and all(isinstance(arg, str) for arg in get_args(_type))


def create_output_model(func: Callable) -> ToolOutput:
    """
    Create an output model for a function based on its return annotation.
    """
    return_type = inspect.signature(func, follow_wrapped=True).return_annotation
    description = "No description provided."

    if return_type is inspect.Signature.empty:
        return ToolOutput(
            available_modes=["null"],
        )

    if hasattr(return_type, "__metadata__"):
        description = return_type.__metadata__[0] if return_type.__metadata__ else None
        return_type = return_type.__origin__

    # Unwrap Optional types
    is_optional = False
    if get_origin(return_type) is Union and type(None) in get_args(return_type):
        return_type = next(arg for arg in get_args(return_type) if arg is not type(None))
        is_optional = True

    wire_type = get_wire_type(return_type)

    available_modes = ["value", "error"]

    if is_optional:
        available_modes.append("null")

    return ToolOutput(
        description=description,
        available_modes=available_modes,
        value_schema=ValueSchema(val_type=wire_type),
    )


def extract_field_info(param: inspect.Parameter) -> dict:
    """
    Extract type and field parameters from a function parameter.

    Args:
        param (inspect.Parameter): The parameter to extract information from.

    Returns:
        dict: A dictionary with 'type' and 'field_params'.
    """
    annotation = param.annotation
    if annotation == inspect.Parameter.empty:
        raise TypeError(f"Parameter {param} has no type annotation.")

    metadata = getattr(annotation, "__metadata__", [])

    default = param.default if param.default is not inspect.Parameter.empty else None
    description = next((m for m in metadata if isinstance(m, str)), None)
    # TODO throw error if no description is provided

    inferrable = next((m.inferrable for m in metadata if isinstance(m, Inferrable)), True)

    # If the param is Annotated[], unwrap the annotation
    # Otherwise, use the literal type
    original_type = annotation.__args__[0] if get_origin(annotation) is Annotated else annotation
    field_type = original_type

    # Unwrap Optional types
    is_optional = False
    if get_origin(field_type) is Union and type(None) in get_args(field_type):
        field_type = next(arg for arg in get_args(field_type) if arg is not type(None))
        is_optional = True

    wire_type = get_wire_type(str) if is_string_literal(field_type) else get_wire_type(field_type)

    field_params = {
        "default": default,
        "optional": is_optional,
        "inferrable": inferrable,
        "description": str(description) if description else "No description provided.",
        "type": field_type,
        "wire_type": wire_type,
        "original_type": original_type,
    }

    return {"type": field_type, "field_params": field_params}


def get_wire_type(
    _type: type,
) -> Literal["string", "integer", "decimal", "boolean", "json"]:
    if issubclass(_type, str):
        return "string"
    elif issubclass(_type, bool):
        return "boolean"
    elif issubclass(_type, int):
        return "integer"
    elif issubclass(_type, float):
        return "decimal"
    elif issubclass(_type, dict):
        return "json"
    else:
        raise TypeError(f"Unsupported parameter type: {_type}")


def determine_output_model(func: Callable) -> type[BaseModel]:
    """
    Determine the output model for a function based on its return annotation.

    Args:
        func (Callable): The function to analyze.

    Returns:
        Type[BaseModel]: A Pydantic model representing the output.
    """
    return_annotation = inspect.signature(func).return_annotation
    output_model_name = f"{snake_to_camel(func.__name__)}Output"
    if return_annotation is inspect.Signature.empty:
        return create_model(output_model_name)
    elif hasattr(return_annotation, "__origin__"):
        if hasattr(return_annotation, "__metadata__"):
            field_type = Optional[return_annotation.__args__[0]]
            description = (
                return_annotation.__metadata__[0] if return_annotation.__metadata__ else ""
            )
            if description:
                return create_model(
                    output_model_name,
                    result=(field_type, Field(description=str(description))),
                )
        else:
            return create_model(
                output_model_name,
                result=(
                    return_annotation,
                    Field(description="No description provided."),
                ),
            )
    else:
        # Handle simple return types (like str)
        return create_model(
            output_model_name,
            result=(return_annotation, Field(description="No description provided.")),
        )


def create_response_model(name: str, output_model: type[BaseModel]) -> type[ResponseModel]:
    """
    Create a response model for the given schema.
    """
    # Create a new response model
    response_model = create_model(
        f"{snake_to_camel(name)}Response",
        code=(int, CustomResponseCode.HTTP_200.code),
        msg=(str, CustomResponseCode.HTTP_200.msg),
        data=(Optional[output_model], None),
    )

    return response_model
