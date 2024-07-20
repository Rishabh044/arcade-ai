from datetime import datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Response


from arcade.actor.core.depends import get_catalog
from arcade.tool.executor import ToolExecutor
from arcade.tool.schemas import ToolDefinition

if TYPE_CHECKING:
    from arcade.tool.catalog import ToolCatalog

router = APIRouter()

api_version = "0.1"


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
