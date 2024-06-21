

import os
import sys
import inspect
from datetime import datetime
from typing import List, Optional, Type, Dict, Annotated, Any, Callable, Tuple
from pathlib import Path
import asyncio

from fastapi import APIRouter
from pydantic import BaseModel, ValidationError, Field, create_model
from importlib import import_module

from arcade.actor.core.conf import settings
from arcade.actor.common.response_code import CustomResponseCode
from arcade.actor.common.response import ResponseModel, response_base
from arcade.apm.base import ToolPack
from arcade.sdk import Param
from arcade.utils import snake_to_camel

class ToolMeta(BaseModel):
    module: str
    path: str
    date_added: datetime = Field(default_factory=datetime.now)
    date_updated: datetime = Field(default_factory=datetime.now)


class ToolSchema(BaseModel):
    name: str
    description: str
    version: str
    tool: Callable

    input_model: Type[BaseModel]
    output_model: Type[BaseModel]

    meta: ToolMeta


class ToolCatalog:
    def __init__(self, tools_dir: str = settings.TOOLS_DIR):
        self.tools = self.read_tools(tools_dir)
        #self.tools.update(self.__get_builitin_tools())

    @staticmethod
    def read_tools(directory: str) -> List[ToolSchema]:
        toolpack = ToolPack.from_lock_file(directory)
        sys.path.append(str(Path(directory).resolve() / 'tools'))

        tools = {}
        for name, tool_spec in toolpack.tools.items():
            print(name, tool_spec)
            module_name, versioned_tool = tool_spec.split('.', 1)
            func_name, version = versioned_tool.split('@')

            module = import_module(module_name)
            tool = getattr(module, func_name)

            tool_meta = ToolMeta(
                module=module_name,
                path=module.__file__
            )

            input_model, output_model = create_func_models(tool)
            response_model = create_response_model(name, output_model)
            tool_schema = ToolSchema(
                name=name,
                description=tool.__doc__,
                version=version,
                tool=tool,
                input_model=input_model,
                output_model=response_model,
                meta=tool_meta
            )
            tools[name] = tool_schema

        return tools

    def __get_builitin_tools(self) -> Dict[str, ToolSchema]:
        tools = {}
        sys.path.append(str(settings.BUILTIN_TOOLS_DIR))

        for tool_spec in settings.BUILTIN_TOOLS:
            print(tool_spec)

            module_name, versioned_tool = tool_spec.split('.', 1)
            func_name, version = versioned_tool.split('@')

            module = import_module(module_name)
            tool = getattr(module, func_name)

            input_model, output_model = create_func_models(tool)
            response_model = create_response_model(func_name, output_model)
            tool_schema = ToolSchema(
                name=func_name,
                description=tool.__doc__,
                version='builtin',
                tool=tool,
                input_model=input_model,
                output_model=response_model,
                meta=ToolMeta(module=module_name, path=module.__file__)
            )
            tools[func_name] = tool_schema

        return tools


    def __getitem__(self, name: str) -> Optional[ToolSchema]:
        #TODO error handling
        for tool_name, tool in self.tools.items():
            if tool_name == name:
                return tool
        return None

    def get_tool(self, name: str) -> Optional[Callable]:
        for tool in self.tools:
            if tool.name == name:
                return tool.tool
        return None

    def list_tools(self) -> List[Dict[str, str]]:
        def get_tool_endpoint(t: ToolSchema) -> str:
            return f"/tool/{t.meta.module}/{t.name}"
        return [
            {'name': t.name,
             'description': t.description,
             'endpoint': get_tool_endpoint(t)
            } for t in self.tools.values()]






def create_func_models(func: Callable) -> Tuple[Type[BaseModel], Type[BaseModel]]:
    """
    Analyze a function to create corresponding Pydantic models for its input and output.

    Args:
        func (Callable): The function to analyze.

    Returns:
        Tuple[Type[BaseModel], Type[BaseModel]]: A tuple containing the input and output Pydantic models.
    """
    input_fields = {}
    if asyncio.iscoroutinefunction(func):
        func = func.__wrapped__
    for name, param in inspect.signature(func, follow_wrapped=True).parameters.items():
        field_info = extract_field_info(param)
        input_fields[name] = (field_info['type'], Field(**field_info['field_params']))

    input_model = create_model(f"{snake_to_camel(func.__name__)}Input", **input_fields)

    output_model = determine_output_model(func)

    return input_model, output_model

def extract_field_info(param: inspect.Parameter) -> dict:
    """
    Extract type and field parameters from a function parameter.

    Args:
        param (inspect.Parameter): The parameter to extract information from.

    Returns:
        dict: A dictionary with 'type' and 'field_params'.
    """
    annotation = param.annotation
    default = param.default if param.default is not inspect.Parameter.empty else None
    description = getattr(annotation, '__metadata__', [None])[0] if hasattr(annotation, '__metadata__') else None

    field_params = {
        'default': default,
        'description': str(description) if description else "No description provided."
    }

    # Handle specific annotations like Param and Secret if needed
    if hasattr(annotation, '__origin__') and annotation.__origin__ in [Param]:
        field_type = annotation.__args__[0]
    else:
        field_type = annotation

    return {'type': field_type, 'field_params': field_params}

def determine_output_model(func: Callable) -> Type[BaseModel]:
    """
    Determine the output model for a function based on its return annotation.

    Args:
        func (Callable): The function to analyze.

    Returns:
        Type[BaseModel]: A Pydantic model representing the output.
    """
    return_annotation = inspect.signature(func).return_annotation
    if return_annotation is inspect.Signature.empty:
        return create_model(f"{snake_to_camel(func.__name__)}Output")
    elif hasattr(return_annotation, '__origin__'):
        if hasattr(return_annotation, '__metadata__'):
            field_type = Optional[return_annotation.__args__[0]]
            description = return_annotation.__metadata__[0] if return_annotation.__metadata__ else ""
            if description:
                return create_model(f"{snake_to_camel(func.__name__)}Output", result=(field_type, Field(description=str(description))))
        else:
            return create_model(f"{snake_to_camel(func.__name__)}Output", result=(return_annotation, Field(description="No description provided.")))

def create_response_model(name: str, output_model: Type[BaseModel]) -> Type[ResponseModel]:
    """
    Create a response model for the given schema.
    """
    # Create a new response model
    response_model = create_model(
        f"{snake_to_camel(name)}Response",
        code=(int, CustomResponseCode.HTTP_200.code),
        msg=(str, CustomResponseCode.HTTP_200.msg),
        data=(Optional[output_model], None)
    )

    return response_model