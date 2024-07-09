from fastapi import APIRouter

from arcade.actor.core.conf import settings
from arcade.actor.routes.tool import router as tool_router

v1 = APIRouter(prefix=settings.API_V1_STR)
v1.include_router(tool_router, prefix="/tools", tags=["Tool Catalog"])
