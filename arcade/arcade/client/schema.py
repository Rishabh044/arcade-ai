from enum import Enum

from pydantic import AnyUrl, BaseModel, Field

from arcade.core.schema import ToolCallOutput, ToolContext


class AuthProvider(str, Enum):
    """The supported authorization providers."""

    oauth2 = "oauth2"
    """OAuth 2.0 authorization"""

    google = "google"
    """Google authorization"""

    slack_user = "slack_user"
    """Slack (user token) authorization"""

    github_app = "github_app"
    """GitHub App authorization"""


class AuthRequest(BaseModel):
    """
    The requirements for authorization for a tool
    """

    authority: AnyUrl | None = None
    """The URL of the OAuth 2.0 authorization server."""

    scope: list[str]
    """The scope(s) needed for authorization."""


class AuthResponse(BaseModel):
    """Response from an authorization request."""

    auth_id: str = Field(alias="authorizationID")
    """The ID of the authorization request"""

    auth_url: str = Field(alias="authorizationURL")
    """The URL for the authorization"""


class AuthStatus(BaseModel):
    """Status of an authorization request."""

    state: str
    """The state of the authorization request"""

    value: ToolContext | None = None
    """The value of the authorization request with token and user ID"""


class ExecuteToolResponse(BaseModel):
    """Response from executing a tool."""

    invocation_id: str
    """The globally-unique ID for this tool invocation in the run."""

    duration: float
    """The duration of the tool invocation in milliseconds."""

    finished_at: str
    """The timestamp when the tool invocation finished."""

    success: bool
    """Whether the tool invocation was successful."""

    output: ToolCallOutput | None = None
    """The output of the tool invocation."""
