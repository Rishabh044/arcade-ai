import os
import sys
import traceback
import inspect
from textwrap import dedent
from typing import List, Optional, Type, Annotated, Dict
from pathlib import Path

from fastapi import APIRouter, Body, Depends, Path, HTTPException
from pydantic import BaseModel, ValidationError, create_model
from importlib import import_module

from arcade.tool.catalog import ToolSchema
from arcade.actor.core.conf import settings
from arcade.actor.common.response_code import CustomResponseCode
from arcade.actor.common.response import ResponseModel, response_base


def create_endpoint_function(name, description, func, input_model, output_model):
    """
    Factory function to create endpoint functions with 'frozen' schema and input_model values.
    """

    async def run(body: input_model):
        try:
            # Execute the action
            result = await func(**body.dict())
            return await response_base.success(data={"result": result})
        except ValidationError as e:
            return await response_base.error(res=CustomResponseCode.HTTP_400, msg=str(e))
        except Exception as e:
            print(traceback.format_exc())
            return await response_base.error(res=CustomResponseCode.HTTP_500, msg=str(e))

    run.__name__ = name
    run.__doc__ = description

    return run



def generate_endpoint(schemas: List[ToolSchema]) -> APIRouter:
    routers = []
    top_level_router = APIRouter(prefix=settings.API_ACTION_STR)

    for schema in schemas:
        router = APIRouter(prefix="/" + schema.meta.module)


        # Create the endpoint function
        run = create_endpoint_function(
            name=schema.name,
            description=schema.description,
            func=schema.tool,
            input_model=schema.input_model,
            output_model=schema.output_model
        )

        # Add the endpoint to the FastAPI app
        router.post(
            f"/{schema.name}",
            name=schema.name,
            summary=schema.description,
            tags=[schema.meta.module],
            response_model=schema.output_model,
            response_model_exclude_unset=True,
            response_model_exclude_none=True,
            response_description=create_output_description(schema.output_model)
            )(run)

        routers.append(router)
    for router in routers:
        top_level_router.include_router(router)
    return top_level_router



def create_output_description(output_model: Type[BaseModel]) -> str:
    """
    Create a description string for the output model.
    """
    if not output_model:
        return None

    output_description = dedent(output_model.__doc__ or "")
    output_description += "\n\n**Attributes:**\n\n"

    for name, field in output_model.model_fields.items():
        output_description += f"- **{name}** ({field.annotation.__name__})\n"

    return output_description