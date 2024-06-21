
from datetime import datetime

from pydantic import BaseModel, Field

from arcade.actor.schemas.base import SchemaBase


class DataSchemaBase(SchemaBase):
    """
    Base schema for Data model.
    """
    file_name: str = Field(..., title="File Name", description="Name of the file")


class CreateDataParam(DataSchemaBase):
    """
    Parameters required to create a Data entry.
    """
    json_blob: str = Field(..., title="JSON Blob", description="JSON blob containing the data")
    file_path: str | None = Field(default=None, title="File Path", description="Path of the file")


class DeleteDataParam(DataSchemaBase):
    """
    Parameters required to delete a Data entry.
    """
    pass


class GetDataObject(DataSchemaBase):
    """
    Schema to retrieve details of a Data entry.
    """
    json_blob: str = Field(..., title="JSON Blob", description="JSON blob containing the data")


class GetDataDetails(DataSchemaBase):
    """
    Schema to retrieve details of a Data entry.
    """
    id: int = Field(..., title="ID", description="Unique identifier of the Data entry")
    file_path: str = Field(..., title="File Path", description="Path of the file")

    created_time: datetime = Field(..., title="Creation Time", description="Time when the Data entry was created")
    updated_time: datetime | None = Field(default=datetime.now(), title="Updated Time", description="Time when the Data entry was last updated")
