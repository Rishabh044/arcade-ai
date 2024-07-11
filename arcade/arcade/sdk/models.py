from abc import ABC
from typing import Literal, Optional, Union

from pydantic import AnyUrl, BaseModel, Field, conlist


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
    value_schema: ValueSchema = Field(
        ...,
        description="The schema of the value of this parameter.",
    )
    inferrable: bool = Field(
        True,
        description="Whether a value for this parameter can be inferred by a model. Defaults to `true`.",
    )


class ToolInput(BaseModel):
    parameters: conlist(InputParameter)


class ToolOutput(BaseModel):
    description: Optional[str] = Field(
        None, description="A descriptive, human-readable explanation of the output."
    )
    available_modes: conlist(
        Literal["value", "error", "null", "artifact", "requires_authorization"], min_length=1
    ) = Field(
        ...,
        description="The available modes for the output.",
        default_factory=lambda: ["value", "error", "null"],
    )
    value_schema: Optional[ValueSchema] = Field(
        None, description="The schema of the value of the output."
    )


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
