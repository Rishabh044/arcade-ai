from typing import Any, Generic, TypeVar

import httpx
from openai import AsyncOpenAI, OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from arcade.client.base import AsyncArcadeClient, BaseResource, SyncArcadeClient
from arcade.client.errors import (
    APIStatusError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
)
from arcade.client.schema import (
    AuthProvider,
    AuthRequest,
    AuthResponse,
    ExecuteToolResponse,
)
from arcade.core.schema import ToolDefinition

T = TypeVar("T")
ClientT = TypeVar("ClientT", SyncArcadeClient, AsyncArcadeClient)


class ChatCompletionsMixin:
    """Mixin for chat completions functionality."""

    def __init__(self, openai_client: OpenAI | AsyncOpenAI):
        self._openai_client = openai_client

    def create(self, *args: Any, **kwargs: Any) -> ChatCompletion | ChatCompletionChunk:
        """Create a chat completion."""
        return self._openai_client.chat.completions.create(*args, **kwargs)


class SyncChatCompletions(ChatCompletionsMixin):
    """Synchronous chat completions."""


class AsyncChatCompletions(ChatCompletionsMixin):
    """Asynchronous chat completions."""

    async def create(self, *args: Any, **kwargs: Any) -> ChatCompletion | ChatCompletionChunk:
        """Create an asynchronous chat completion."""
        return await self._openai_client.chat.completions.create(*args, **kwargs)


class AuthResource(BaseResource[ClientT]):
    """Authentication resource."""

    _base_path = "/v1/auth"

    def authorize(
        self,
        provider: AuthProvider,
        scopes: list[str],
        user_id: str,
        authority: str | None = None,
    ) -> AuthResponse:
        """
        Initiate an authorization request.

        Args:
            provider: The authorization provider.
            scopes: The scopes required for the authorization.
            user_id: The user ID initiating the authorization.
            authority: The authority initiating the authorization.
        """
        auth_provider = provider.value

        body = {
            "auth_requirement": {
                "provider": auth_provider,
                auth_provider: AuthRequest(scope=scopes, authority=authority).dict(
                    exclude_none=True
                ),
            },
            "user_id": user_id,
        }

        data = self._client._execute_request(  # type: ignore[attr-defined]
            "POST",
            f"{self._base_path}/authorize",
            json=body,
        )
        return AuthResponse(**data)

    def poll_authorization(self, auth_id: str) -> AuthResponse:
        """
        Poll for the status of an authorization request.

        Args:
            auth_id: The authorization ID.

        Example:
            auth_status = client.auth.poll_authorization("auth_123")
        """
        data = self._client._execute_request(  # type: ignore[attr-defined]
            "GET", f"{self._base_path}/status", params={"authorizationID": auth_id}
        )
        return AuthResponse(**data)


class ToolResource(BaseResource[ClientT]):
    """Tool resource."""

    _base_path = "/v1/tools"

    def run(
        self,
        tool_name: str,
        user_id: str,
        tool_version: str | None = None,
        inputs: dict[str, Any] | None = None,
    ) -> ExecuteToolResponse:
        """
        Send a request to execute a tool and return the response.

        Args:
            tool_name: The name of the tool to execute.
            user_id: The user ID initiating the tool execution.
            tool_version: The version of the tool to execute (if not provided, the latest version will be used).
            inputs: The inputs for the tool.
        """
        request_data = {
            "tool_name": tool_name,
            "user_id": user_id,
            "tool_version": tool_version,
            "inputs": inputs,
        }
        data = self._client._execute_request(  # type: ignore[attr-defined]
            "POST", f"{self._base_path}/execute", json=request_data
        )
        return ExecuteToolResponse(**data)

    def get(self, director_id: str, tool_id: str) -> ToolDefinition:
        """
        Get the specification for a tool.

        Args:
            director_id: The director ID.
            tool_id: The tool ID.
        """
        data = self._client._execute_request(  # type: ignore[attr-defined]
            "GET",
            f"{self._base_path}/definition",
            params={"director_id": director_id, "tool_id": tool_id},
        )
        return ToolDefinition(**data)


class ArcadeClientMixin(Generic[ClientT]):
    """Mixin for Arcade clients."""

    def __init__(self, base_url: str, *args: Any, **kwargs: Any):
        super().__init__(base_url, *args, **kwargs)
        self._openai_client: OpenAI | AsyncOpenAI | None = None
        self.auth = AuthResource(self)  # type: ignore[type-var, var-annotated]
        self.tool = ToolResource(self)  # type: ignore[type-var, var-annotated]
        self.chat: SyncChatCompletions | AsyncChatCompletions | None = None

    def _handle_http_error(
        self,
        e: httpx.HTTPStatusError,
        error_map: dict[int, type[APIStatusError]],
    ) -> None:
        status_code = e.response.status_code
        error_class = error_map.get(status_code, InternalServerError)
        raise error_class(str(e), response=e.response)


class SyncArcade(ArcadeClientMixin[SyncArcadeClient], SyncArcadeClient):
    """Synchronous Arcade client."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._openai_client = OpenAI(base_url=self._base_url)
        self.chat = SyncChatCompletions(self._openai_client)

    def _execute_request(self, method: str, url: str, **kwargs: Any) -> Any:
        """
        Execute a synchronous request.

        Args:
            method: The HTTP method.
            url: The URL to request.
            **kwargs: Additional arguments for the request.
        """
        try:
            response = self._request(method, url, **kwargs)
            return response.json()
        except httpx.HTTPStatusError as e:
            self._handle_http_error(
                e,
                {
                    400: BadRequestError,
                    401: AuthenticationError,
                    403: PermissionDeniedError,
                    404: NotFoundError,
                    500: InternalServerError,
                },
            )


class AsyncArcade(ArcadeClientMixin[AsyncArcadeClient], AsyncArcadeClient):
    """Asynchronous Arcade client."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._openai_client = AsyncOpenAI(base_url=self._base_url)
        self.chat = AsyncChatCompletions(self._openai_client)

    async def _execute_request(self, method: str, url: str, **kwargs: Any) -> Any:
        """
        Execute an asynchronous request.

        Args:
            method: The HTTP method.
            url: The URL to request.
            **kwargs: Additional arguments for the request.
        """
        try:
            response = await self._request(method, url, **kwargs)
            return response.json()
        except httpx.HTTPStatusError as e:
            self._handle_http_error(
                e,
                {
                    400: BadRequestError,
                    401: AuthenticationError,
                    403: PermissionDeniedError,
                    404: NotFoundError,
                    500: InternalServerError,
                },
            )
