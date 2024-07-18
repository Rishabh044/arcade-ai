from datetime import datetime
from typing import TYPE_CHECKING, ClassVar, Union

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from arcade.actor.core.depends import get_catalog
from arcade.tool.executor import ToolExecutor
from arcade.tool.schemas import ToolDefinition

if TYPE_CHECKING:
    from arcade.tool.catalog import ToolCatalog

router = APIRouter()

api_version = "0.1"


class ToolVersion(BaseModel):
    name: str
    version: str


class InvokeToolRequest(BaseModel):
    run_id: str
    invocation_id: str
    created_at: str
    tool: ToolVersion
    input: dict | None
    context: dict | None


class ToolOutputError(BaseModel):
    message: str
    developer_message: str | None = None


class ToolOutput(BaseModel):
    value: Union[str, int, float, bool, dict] | None = None
    error: ToolOutputError | None = None

    class Config:
        json_schema_extra: ClassVar[dict] = {
            "oneOf": [
                {"required": ["value"]},
                {"required": ["error"]},
                {"required": ["requires_authorization"]},
                {"required": ["artifact"]},
            ]
        }


class InvokeToolResponse(BaseModel):
    invocation_id: str
    finished_at: str
    success: bool
    output: ToolOutput | None = None


@router.get("/healthy", summary="Check if the actor is healthy")
async def is_healthy(response: Response):
    response.headers["Arcade-Api-Version"] = api_version
    return {"status": "ok"}


@router.get("/tools", summary="Get the actor's tool catalog", response_model_exclude_none=True)
async def list_tools(
    response: Response, catalog: "ToolCatalog" = Depends(get_catalog)
) -> list[ToolDefinition]:
    response.headers["Arcade-Api-Version"] = api_version
    return [tool.definition for tool in catalog]


@router.post("/tools/invoke", summary="Invoke a tool", response_model_exclude_none=True)
async def invoke_tool(
    request: InvokeToolRequest, catalog: "ToolCatalog" = Depends(get_catalog)
) -> InvokeToolResponse:
    tool = catalog[request.tool.name]

    body = request.input
    response = await ToolExecutor.run(tool.tool, tool.input_model, tool.output_model, **body)

    if response.code == 200:
        output = ToolOutput(value=response.data.result)
    else:
        output = ToolOutput(error=ToolOutputError(message=response.msg))

    return InvokeToolResponse(
        invocation_id=request.invocation_id,
        finished_at=datetime.now().isoformat(),
        success=response.code == 200,
        output=output,
    )
