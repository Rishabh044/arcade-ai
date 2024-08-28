from typing import Any, Type

from langchain.tools import BaseTool
from langchain_community.agent_toolkits.base import BaseToolkit
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, create_model

from arcade.core.catalog import Catalog, MaterializedTool
from arcade.core.executor import ToolExecutor
from arcade.core.schema import ToolContext


class ArcadeToolKit(BaseToolkit):
    """Toolkit for using Arcade tools in Langchain"""

    def __init__(self, catalog: Catalog):
        self.catalog = catalog

    def get_tools(self) -> list[BaseTool]:
        return [LangchainAdapter(t) for t in self.catalog.tools]


class LangchainAdapter(BaseTool):
    def __init__(self, arcade_tool: MaterializedTool, **kwargs: Any):
        self.arcade_tool = arcade_tool
        super().__init__(
            name=arcade_tool.name,
            description=arcade_tool.definition.description,
            **kwargs,
        )

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        tool_input = kwargs if kwargs else args[0]
        result = ToolExecutor.run(
            self.arcade_tool.tool,
            self.arcade_tool.definition,
            self.arcade_tool.input_model,
            self.arcade_tool.output_model,
            ToolContext(),
            **tool_input,
        )
        return result.data.result if result.data else result.msg

    async def _arun(self, *args: Any, **kwargs: Any) -> Any:
        tool_input = kwargs if kwargs else args[0]
        result = await ToolExecutor.run(
            self.arcade_tool.tool,
            self.arcade_tool.definition,
            self.arcade_tool.input_model,
            self.arcade_tool.output_model,
            ToolContext(),
            **tool_input,
        )
        return result.data.result if result.data else result.msg

    def _authorize(self, **kwargs: Any) -> ToolContext:
        if self.arcade_tool.requires_auth:
            # TODO get auth here?
            return ToolContext()

    def args_schema(self) -> Type[BaseModel]:
        original_model = self.arcade_tool.input_model
        new_fields = {**original_model.__fields__, "config": (RunnableConfig, None)}
        return create_model(f"LC{original_model.__name__}", **new_fields)
