from abc import ABC
from typing import Literal, Optional, Union

from pydantic import AnyUrl, BaseModel, Field, conlist


class Inferrable:
    def __init__(self, inferrable: bool):
        self.inferrable = inferrable


class ValueSchema(BaseModel):
    type: Literal["string", "integer", "decimal", "boolean", "json"]
    enum: Optional[list[str]] = None


class InputParameter(BaseModel):
    name: str = Field(..., description="The human-readable name of this parameter.")
    required: bool = Field(
        ..., description="Whether this parameter is required (true) or optional (false)."
    )
    description: Optional[str] = Field(
        None, description="A descriptive, human-readable explanation of the parameter."
    )
    value_schema: ValueSchema
    inferrable: Optional[bool] = Field(
        True,
        description="Whether a value for this parameter can be inferred by a model. Defaults to `true`.",
    )


class ToolInput(BaseModel):
    parameters: conlist(InputParameter)


class OutputValue(BaseModel):
    description: Optional[str]
    value_schema: ValueSchema


class ToolOutput(BaseModel):
    available_modes: conlist(
        Literal["value", "error", "null", "artifact", "requires_authorization"], min_length=1
    ) = Field(
        ...,
        description="The available modes for the output.",
        default_factory=lambda: ["value", "error", "null"],
    )
    value: Optional[OutputValue] = None


class ToolAuthorizationRequirement(BaseModel, ABC):
    pass


class OAuth2AuthorizationRequirement(ToolAuthorizationRequirement):
    url: AnyUrl
    scopes: Optional[list[str]] = None


class ToolRequirements(BaseModel):
    authorization: Union[ToolAuthorizationRequirement, None] = None


class ToolDefinition(BaseModel):
    name: str
    description: str
    version: str
    input: ToolInput
    output: ToolOutput
    requirements: ToolRequirements
