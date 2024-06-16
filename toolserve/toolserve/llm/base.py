from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union, Literal, Any, AsyncGenerator
import uuid
import time
import httpx

# ---- Completion Request ----

class ChatMessage(BaseModel):
    role: Literal['system', 'user', 'assistant']
    content: str

# Define options for the response format
class ResponseFormat(BaseModel):
    type: Literal["text", "json_object"]

# Define stream options for streaming API calls
class ChatStreamOptions(BaseModel):
    max_chunk_size: int
    delay_between_chunks: float


class ToolDefinition(BaseModel):
    name: str
    """The name of the function to be called.

    Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length
    of 64.
    """
    description: str
    """
    A description of what the function does, used by the model to choose when and
    how to call the function.
    """
    parameters: str
    """The parameters the functions accepts, described as a JSON Schema object"""

class Tools(BaseModel):
    type: str = "function"
    function: ToolDefinition


class CompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[Dict[str, int]] = None
    logprobs: Optional[bool] = None
    max_tokens: Optional[int] = None
    n: Optional[int] = None
    presence_penalty: Optional[float] = None
    response_format: Optional[ResponseFormat] = None
    seed: Optional[int] = None
    stop: Optional[Union[str, List[str]]] = None
    stream_options: Optional[ChatStreamOptions] = None
    temperature: Optional[float] = None
    tools: Optional[Union[List[Tools], List[str]]] = None
    tool_choice: Optional[str] = None
    top_logprobs: Optional[int] = None
    top_p: Optional[float] = None
    user: Optional[str] = None
    stream: Optional[bool] = False




# ------ Completion Response --------

# Define the response choice model for different types of content in responses
class Choice(BaseModel):
    finish_reason: Optional[str] = None
    index: Optional[int] = None
    message: Optional[Dict[str, Union[str, Dict]]] = None

# Define usage statistics for tracking API consumption
class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


# Define the model response class
class CompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    choices: List[Choice]
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    object: str  # Type of object, like "text_completion"
    system_fingerprint: Optional[str] = None
    usage: Usage


class ProviderConfig(BaseModel):
    base_url: str
    auth: bool = True
    api_key: Optional[str] = None


class ModelProvider:

    def __init__(self, config: Optional[ProviderConfig] = None):
        self.config = config or ProviderConfig()
        self.client = httpx.AsyncClient()

    async def _send_request(self, endpoint: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.config.base_url}/{endpoint}"
        if self.config.auth:
            headers = {'Authorization': f'Bearer {self.config.api_key}'}
        else:
            headers = {}
        try:
            if method == 'POST':
                response = await self.client.post(url, json=data, headers=headers)
            else:
                response = await self.client.get(url, params=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logging.error(f"Request failed: {e}")
            raise

    async def _stream_request(self, endpoint: str, method: str, data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        url = f"{self.config.base_url}/{endpoint}"
        headers = {'Authorization': f'Bearer {self.config.api_key}'}
        async with self.client.stream(method, url, json=data, headers=headers) as response:
            response.raise_for_status()
            async for part in response.aiter_text():
                yield json.loads(part)

    def get_allowed_models(self):
        raise NotImplementedError

    async def chat(self, request: CompletionRequest) -> CompletionResponse:
        raise NotImplementedError

    async def stream_chat(self, request: CompletionRequest) -> AsyncGenerator[CompletionResponse, None]:
        raise NotImplementedError

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        raise NotImplementedError

    async def stream_complete(self, request: CompletionRequest) -> AsyncGenerator[CompletionResponse, None]:
        raise NotImplementedError



class OpenAIConfig(ProviderConfig):
    auth: bool = True
    base_url: str = "https://api.openai.com/v1"


class OpenAIProvider(ModelProvider):

    def __init__(self):
        super().__init__(config=OpenAIConfig())

    def get_allowed_models(self):
        return ["gpt-4-turbo"]

    async def chat(self, request: CompletionRequest) -> CompletionResponse:
        endpoint = 'chat/completions'
        response_data = await self._send_request(endpoint, 'POST', request.dict())
        return CompletionResponse(**response_data)

    async def stream_chat(self, request: CompletionRequest) -> AsyncGenerator[CompletionResponse, None]:
        raise NotImplementedError

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        raise NotImplementedError

    async def stream_complete(self, request: CompletionRequest) -> AsyncGenerator[CompletionResponse, None]:
        raise NotImplementedError




"""
# Implementation of OllamaLM
class OllamaLM(BaseLM):
    # https://github.com/ollama/ollama/blob/main/docs/api.md

    class OllamaChatConfig(BaseLM.ModelConfig):
        model: str = "llama2"
        api_base="http://localhost:11434",
        api_key: Optional[str] = None,
        mirostat: Optional[int] = None
        mirostat_eta: Optional[float] = None
        mirostat_tau: Optional[float] = None
        num_ctx: Optional[int] = None
        num_gqa: Optional[int] = None
        num_thread: Optional[int] = None
        repeat_last_n: Optional[int] = None
        repeat_penalty: Optional[float] = None
        temperature: Optional[float] = None
        seed: Optional[int] = None
        stop: Optional[List[str]] = None
        tfs_z: Optional[float] = None
        num_predict: Optional[int] = None
        top_k: Optional[int] = None
        top_p: Optional[float] = None
        system: Optional[str] = None
        template: Optional[str] = None


    class OllamaChatRequest(BaseLM.ModelRequest):
        max_tokens: Optional[int] = None
        temperature: Optional[float] = None
        top_p: Optional[float] = None
        frequency_penalty: Optional[float] = None
        stop: Optional[List[str]] = None
        tools: Optional[Dict[str, Any]] = None
        tool_choice: Optional[str] = None
        response_format: Optional[ResponseFormat] = None

    class OllamaChatResponse(BaseLM.ModelResponse):



    async def invoke(self, request: LMRequest) -> LMResponse:
        endpoint = 'api/chat'  # Assuming this is the endpoint for the chat API
        data = {
            'model': self.config.model,
            'messages': request.messages,
            'options': request.params
        }
        response_data = await self._send_request(endpoint, 'POST', data)
        return LMResponse(**response_data)

    async def astream(self, request: LMRequest) -> LMResponse:
        endpoint = 'api/stream'  # Assuming a different endpoint for streaming
        data = {
            'model': self.config.model,
            'messages': request.messages,
            'options': request.params,
            'stream': True
        }
        async with self._stream_request(endpoint, 'POST', data) as stream:
            response.raise_for_status()
            # Collect streaming data and return as part of LMResponse
            all_data = []
            async for part in response.aiter_text():
                all_data.append(json.loads(part))
            return LMResponse(
                choices=all_data,
                created=int(time.time()),
                model=self.config.model,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
 """