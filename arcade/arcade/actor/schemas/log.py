from datetime import datetime

from pydantic import ConfigDict, Field

from arcade.actor.schemas.base import SchemaBase


class LogSchemaBase(SchemaBase):
    level: str = Field(..., title='Log level', description='Log level')
    msg: str = Field(..., title='Log message', description='Log message')


class CreateLog(LogSchemaBase):
    pass


class GetLogDetails(LogSchemaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_time: datetime
    updated_time: datetime | None = None
