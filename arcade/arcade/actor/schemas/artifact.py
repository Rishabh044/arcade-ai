from datetime import datetime

from pydantic import ConfigDict, Field

from arcade.actor.schemas.base import SchemaBase


class ArtifactSchemaBase(SchemaBase):
    name: str
    file_path: str


class CreateArtifactParam(ArtifactSchemaBase):
    data: bytes
    media_type: str


class DeleteArtifactParam(ArtifactSchemaBase):
    pass

class UpdateArtifactParam(ArtifactSchemaBase):
    pass

class GetArtifactDetails(ArtifactSchemaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_time: datetime
    updated_time: datetime | None = None
