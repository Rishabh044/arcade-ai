from pydantic import BaseModel


class ToolDefinition(BaseModel):
    name: str
    description: str
    version: str
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    # requirements: Optional[ToolRequirements]
