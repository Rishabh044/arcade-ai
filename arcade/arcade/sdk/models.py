from abc import ABC
from typing import Optional, Union

from pydantic import AnyUrl, BaseModel


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
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    requirements: ToolRequirements
