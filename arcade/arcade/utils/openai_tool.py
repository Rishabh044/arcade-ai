import json
from typing import Any, Dict, Type
from pydantic import BaseModel
from pydantic_core import PydanticUndefined
from enum import Enum


from arcade.tool.catalog import ToolSchema

PYTHON_TO_JSON_TYPES = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}

def python_type_to_json_type(python_type: Type) -> Dict[str, Any]:
    """
    Map Python types to JSON Schema types, including handling of complex types such as lists and dictionaries.

    Args:
        python_type (Type): The Python type to be converted to a JSON schema type.

    Returns:
        Dict[str, Any]: A dictionary representing the JSON schema for the given Python type.
    """
    if hasattr(python_type, '__origin__'):
        origin = python_type.__origin__


        if origin is list:
            item_type = python_type_to_json_type(python_type.__args__[0])
            return {'type': 'array', 'items': item_type}
        elif origin is dict:
            value_type = python_type_to_json_type(python_type.__args__[1])
            return {'type': 'object', 'additionalProperties': value_type}

    elif issubclass(python_type, BaseModel):
        return model_to_json_schema(python_type)

    return PYTHON_TO_JSON_TYPES.get(python_type, "string")

def model_to_json_schema(model: Type[BaseModel]) -> Dict[str, Any]:
    """
    Convert a Pydantic model to a JSON schema.

    Args:
        model (Type[BaseModel]): The Pydantic model to convert.

    Returns:
        Dict[str, Any]: A dictionary representing the JSON schema for the given model.
    """
    properties = {}
    required = []
    for field_name, model_field in model.model_fields.items():
        type_json = python_type_to_json_type(model_field.annotation)
        if isinstance(type_json, dict):
            field_schema = type_json
        else:
            field_schema = {
                "type": type_json,
                "description": model_field.description or "",
            }
        if model_field.default not in [None, PydanticUndefined]:
            if isinstance(model_field.default, Enum):
                field_schema["default"] = model_field.default.value
            else:
                field_schema["default"] = model_field.default
        if model_field.is_required():
            required.append(field_name)
        properties[field_name] = field_schema
    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }

def schema_to_openai_tool(tool_schema: 'ToolSchema') -> str:
    """Convert an ToolSchema object to a JSON schema string in the specified function format.

    Example output format:
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"]
                    }
                },
                "required": ["location"]
            }
        }
    }

    Args:
        tool_schema (ToolSchema): The tool schema to convert.

    Returns:
        str: A JSON schema string representing the tool in the specified format.
    """
    input_model_schema = model_to_json_schema(tool_schema.input_model)
    function_schema = {
        "type": "function",
        "function": {
            "name": tool_schema.name,
            "description": tool_schema.description,
            "parameters": input_model_schema,
        }
    }
    return json.dumps(function_schema, indent=2)
