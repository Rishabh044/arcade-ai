from datetime import datetime
from typing import ClassVar, Union
from arcade.core.catalog import ToolCatalog
from arcade.core.executor import ToolExecutor
from arcade.core.tool import ToolDefinition
from arcade.core.toolkit import Toolkit
from fastapi import Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel
from openai import AsyncOpenAI


client = AsyncOpenAI(base_url="http://localhost:6901")

app = FastAPI()
api_version = "0.1"


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": request.message},
            ],
            model="gpt-4o-mini",
            max_tokens=150,
            tool_choice="execute",
        )
        return {"response": chat_completion.choices[0].message.content.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


catalog = ToolCatalog()
# router = generate_endpoint(list(catalog.tools.values()))
# app.include_router(router)
# app.state.catalog = catalog

arithmetic_toolkit = Toolkit.from_directory(".")
catalog.add_toolkit(arithmetic_toolkit)


@app.get("/actor/healthy", summary="Check if the actor is healthy")
async def is_healthy(response: Response):
    response.headers["Arcade-Api-Version"] = api_version
    return {"status": f"ok, {len(catalog.tools)} tool(s) loaded"}


@app.get(
    "/actor/tools",
    summary="Get the actor's tool catalog",
    response_model_exclude_none=True,
)
async def list_tools(response: Response) -> list[ToolDefinition]:
    response.headers["Arcade-Api-Version"] = api_version
    return [tool.definition for tool in catalog]


@app.post(
    "/actor/tools/invoke", summary="Invoke a tool", response_model_exclude_none=True
)
async def invoke_tool(request: InvokeToolRequest) -> InvokeToolResponse:
    tool = catalog[request.tool.name]

    body = request.input
    response = await ToolExecutor.run(
        tool.tool, tool.input_model, tool.output_model, **body
    )

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
