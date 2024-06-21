
from typing import Annotated
from fastapi import APIRouter, Path, Query
from arcade.actor.schemas.data import (
    CreateDataParam,
    DataSchemaBase,
    GetDataDetails,
    GetDataObject
)
from arcade.actor.services.data_service import data_service
from arcade.actor.common.response import ResponseModel, response_base
from arcade.actor.common.serializers import select_as_dict

router = APIRouter()

# Get data details by data id
@router.get('/{pk}', summary='Get data details')
async def get_data(
    pk: Annotated[int, Path(...)],
) -> ResponseModel:
    data_entry = await data_service.get(pk=pk)
    data = GetDataDetails(**await select_as_dict(data_entry))
    return await response_base.success(data=data)

@router.get('', summary='Get all data files')
async def get_all_data() -> ResponseModel:
    data = await data_service.get_all_data()
    all_data = [GetDataDetails(**await select_as_dict(data_entry)) for data_entry in data]
    return await response_base.success(data=all_data)

# Create a new data entry
@router.post('', summary='Create data')
async def create_data(
    obj: CreateDataParam
) -> ResponseModel:
    data_obj = await data_service.create(obj=obj)
    data = {
        "id": data_obj.id,
        "file_path": data_obj.file_path
    }
    return await response_base.success(data=data)

# Delete data
@router.delete('', summary='Delete data')
async def delete_data(pk: Annotated[list[int], Query(...)]) -> ResponseModel:
    count = await data_service.delete(pk=pk)
    if count > 0:
        return await response_base.success()
    return await response_base.fail()

@router.get('/object/{pk}', summary='Get data object')
async def get_data_object(
    pk: Annotated[int, Path(...)],
) -> ResponseModel:
    """
    Retrieve a data object by its primary key using the GetDataObject schema.

    Args:
        pk (int): The primary key of the data object to retrieve.

    Returns:
        ResponseModel: The response model containing the data object or an error message.
    """
    data_entry = await data_service.get(pk=pk)
    obj = await select_as_dict(data_entry)
    try:
        with open(obj["file_path"], 'r', encoding='utf-8') as file:
            json_data = file.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except IOError:
        raise HTTPException(status_code=500, detail="File read error")

    data_object = GetDataObject(
        file_name=obj["file_name"],
        file_path=obj["file_path"],
        json_blob=json_data
    )
    return await response_base.success(data=data_object)
