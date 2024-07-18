from typing import TYPE_CHECKING

from fastapi import APIRouter, Body, Depends, Query
from pydantic import ValidationError

from arcade.actor.common.response import ResponseModel, response_base
from arcade.actor.common.response_code import CustomResponseCode
from arcade.actor.core.depends import get_catalog
from arcade.tool.openai import schema_to_openai_tool

if TYPE_CHECKING:
    from arcade.tool.catalog import ToolCatalog

router = APIRouter()


@router.get("/healthy", summary="Check if the actor is healthy")
async def is_healthy():
    return {"status": "ok"}


@router.get("/tools", summary="Get the actor's tool catalog")
async def list_tools(catalog: "ToolCatalog" = Depends(get_catalog)):
    return [tool.definition for tool in catalog]
