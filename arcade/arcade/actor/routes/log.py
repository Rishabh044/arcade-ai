
from typing import Annotated
from fastapi import APIRouter, Path, Query
from arcade.actor.schemas.log import CreateLog, LogSchemaBase, GetLogDetails
from arcade.actor.services.log_service import log_service
from arcade.actor.common.response import ResponseModel, response_base
from arcade.actor.common.serializers import select_as_dict

router = APIRouter()

# Get log details by log id
@router.get('/{pk}', summary='Get log details')
async def get_log(
    pk: Annotated[int, Path(...)],
) -> ResponseModel:
    log = await log_service.get(pk=pk)
    data = GetLogDetails(**await select_as_dict(log))
    return await response_base.success(data=data)

# Create a new log
@router.post('', summary='Create log')
async def create_log(
    obj: CreateLog
) -> ResponseModel:
    await log_service.create(obj=obj)
    return await response_base.success()

# Delete log
@router.delete('', summary='Delete log')
async def delete_log(pk: Annotated[list[int], Query(...)]) -> ResponseModel:
    count = await log_service.delete(pk=pk)
    if count > 0:
        return await response_base.success()
    return await response_base.fail()

# Get all logs
@router.get('', summary='Get all logs')
async def get_all_logs() -> ResponseModel:
    data = await log_service.get_log_list()
    return await response_base.success(data=data)
