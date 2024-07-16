from typing import Any, Callable

from pydantic import BaseModel, ValidationError

from arcade.tool.errors import (
    ToolExecutionError,
    ToolInputError,
    ToolOutputError,
    ToolSerializationError,
)
from arcade.tool.response import ToolResponse, tool_response


class ToolExecutor:
    @staticmethod
    async def run(
        func: Callable,
        input_model: BaseModel,
        output_model: BaseModel,
        *args: Any,
        **kwargs: Any,
    ) -> ToolResponse:
        try:
            # serialize the input model
            inputs = await ToolExecutor._serialize_input(input_model, **kwargs)

            # execute the tool function
            results = await func(**inputs.dict())

            # serialize the output model
            output = await ToolExecutor._serialize_output(output_model, results)

            # return the output
            return await tool_response.success(data=output)

        except ToolSerializationError as e:
            return await tool_response.fail(msg=str(e))

        except ToolExecutionError as e:
            return await tool_response.fail(msg=str(e))

        # if we get here we're in trouble
        # TODO: Debate if this is necessary
        except Exception as e:
            return await tool_response.fail(msg=str(e))

    @staticmethod
    async def _serialize_input(input_model: BaseModel, **kwargs: Any) -> BaseModel:
        try:
            # TODO Logging and telemetry

            # build in the input model to the tool function
            inputs = input_model(**kwargs)

        except ValidationError as e:
            raise ToolInputError(msg=str(e))

        return inputs

    @staticmethod
    async def _serialize_output(output_model: BaseModel, results: dict) -> BaseModel:
        # TODO how to type this the results object?
        try:
            # TODO Logging and telemetry

            # build the output model
            output = output_model(**{"result": results})

        except ValidationError as e:
            raise ToolOutputError(msg=str(e))

        return output
