import json
from enum import Enum
from typing import Any, Optional

from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from arcade.core.catalog import MaterializedTool

PYTHON_TO_JSON_TYPES: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def python_type_to_json_type(python_type: type[Any]) -> dict[str, Any]:
    """
    Map Python types to JSON Schema types, including handling of
    complex types such as lists and dictionaries.
    """
    if hasattr(python_type, "__origin__"):
        origin = python_type.__origin__

        if origin is list:
            item_type = python_type_to_json_type(python_type.__args__[0])
            return {"type": "array", "items": item_type}
        elif origin is dict:
            value_type = python_type_to_json_type(python_type.__args__[1])
            return {"type": "object", "additionalProperties": value_type}

    elif issubclass(python_type, BaseModel):
        return model_to_json_schema(python_type)

    return PYTHON_TO_JSON_TYPES.get(python_type, "string")


def model_to_json_schema(model: type[BaseModel]) -> dict[str, Any]:
    """
    Convert a Pydantic model to a JSON schema.
    """
    properties = {}
    required = []
    for field_name, model_field in model.model_fields.items():
        type_json = python_type_to_json_type(model_field.annotation)  # type: ignore[arg-type]
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


def schema_to_openai_tool(tool: MaterializedTool) -> dict[str, Any]:
    """
    Convert a ToolDefinition object to a JSON schema dictionary in the specified function format.
    """
    input_model_schema = model_to_json_schema(tool.input_model)
    function_schema = {
        "type": "function",
        "function": {
            "name": tool.definition.name,
            "description": tool.definition.description,
            "parameters": input_model_schema,
        },
    }
    return function_schema


class EngineClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        api_key = "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"
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def __getattr__(self, name: str):
        return getattr(self.client, name)

    def infer_tool_args(
        self,
        tool: MaterializedTool,
        tool_choice: str,
        model: str,
        messages: Optional[list[dict[str, Any]]] = None,
        prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Infer the arguments for a given tool and call the OpenAI API.
        """
        tool_specification = schema_to_openai_tool(tool)
        if messages is None and prompt is not None:
            messages = [{"role": "user", "content": prompt}]
        try:
            completion = self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=[tool_specification],
                tool_choice=tool_choice,
                **kwargs,
            )
            tool_args = json.loads(completion.choices[0].message.tool_calls[0].function.arguments)

        except (KeyError, IndexError) as e:
            raise ValueError("Invalid response format from OpenAI API.") from e
        return tool_args


class AsyncEngineClient:
    def __init__(self, api_key: str, base_url: str | None = None):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    def __getattr__(self, name: str):
        return getattr(self.client, name)

    async def infer_tool_args(
        self,
        tool: MaterializedTool,
        tool_choice: str,
        model: str,
        messages: Optional[list[dict[str, Any]]] = None,
        prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Infer the arguments for a given tool and call the OpenAI API.
        """
        tool_specification = schema_to_openai_tool(tool)
        if messages is None and prompt is not None:
            messages = [{"role": "user", "content": prompt}]
        try:
            completion = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=[tool_specification],
                tool_choice=tool_choice,
                **kwargs,
            )
            tool_args = json.loads(completion.choices[0].message.tool_calls[0].function.arguments)
        except (KeyError, IndexError) as e:
            raise ValueError("Invalid response format from OpenAI API.") from e
        return tool_args
