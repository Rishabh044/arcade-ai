
from typing import Annotated
from fastapi import APIRouter, Path, Query
from fastapi.responses import StreamingResponse
from toolserve.server.common.response import ResponseModel, response_base
from toolserve.server.common.serializers import select_as_dict

# to take out later
import openai
import json

from pydantic import BaseModel, Field
from typing import List, Optional, Union, Literal, Iterable

from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_stream_options_param import ChatCompletionStreamOptionsParam
from openai.types.chat.chat_completion_tool_choice_option_param import ChatCompletionToolChoiceOptionParam
from openai.types.chat.chat_completion_function_call_option_param import ChatCompletionFunctionCallOptionParam
from openai.types import shared_params
from openai.types.chat_model import ChatModel
from fastapi import Request, HTTPException, status, Depends

from toolserve.server.core.depends import get_catalog
from toolserve.utils.openai_tool import schema_to_openai_tool
from toolserve.llm.base import (
    CompletionResponse,
    CompletionRequest,
    OpenAIProvider,
)

router = APIRouter()


def get_api_key(request: Request) -> str:
    """
    Extracts the API key from the Authorization header as a Bearer token.

    Args:
        request (Request): The request object from which the API key is extracted.

    Returns:
        str: The API key extracted from the Authorization header.

    Raises:
        HTTPException: If the Authorization header is missing or improperly formatted.
    """
    auth_header = request.headers.get('Authorization')
    if auth_header is None or not auth_header.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Authorization token is missing or improperly formatted'
        )
    api_key = auth_header.split(' ')[1]
    return api_key


@router.post(
    '/completions',
    summary='Chat Completions Endpoints mimicking OpenAI',
    response_model=CompletionResponse
)
async def create_chat_completion(
    completion: CompletionRequest,
    api_key: str = Depends(get_api_key),
    catalog=Depends(get_catalog),
) -> CompletionResponse:
    """
    Create a chat completion
    """
    try:
        # select the model
        model = completion.model
        # select the provider from the model
        provider = OpenAIProvider()
        if provider.config.auth:
            provider.config.api_key = api_key

        exe = False
        if completion.tools:
            if isinstance(completion.tools[0], str):
                specs = []
                for tool in completion.tools:
                    specs.append(json.loads(schema_to_openai_tool(catalog[tool])))
                completion.tools = specs
                if completion.tool_choice == "execute":
                    exe = True
                    completion.tool_choice == "required"
        print(completion)
        # send the request to the provider
        response = await provider.chat(completion)

        if exe:
            tool_args = response.choices[0].message
            print(tool_args)

        # TODO background task to save input and output if tool calls for it

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))