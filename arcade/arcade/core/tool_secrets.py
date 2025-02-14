from pydantic import BaseModel, ConfigDict


class ToolSecret(BaseModel):
    """Marks a tool as requiring a named secret."""

    model_config = ConfigDict(frozen=True)

    key_id: str
    """The ID of the secret."""
