from fastapi import APIRouter
from toolserve.server.core.conf import settings
from toolserve.server.routes.tool import router as tool_router
from toolserve.server.routes.data import router as data_router
from toolserve.server.routes.artifact import router as artifact_router
from toolserve.server.routes.log import router as log_router
from toolserve.server.routes.chat import router as chat_router

v1 = APIRouter(prefix=settings.API_V1_STR)
v1.include_router(tool_router, prefix="/tools", tags=["Tool Catalog"])
v1.include_router(data_router, prefix="/data", tags=["Data Management"])
v1.include_router(artifact_router, prefix="/artifact", tags=["Artifact Management"])
v1.include_router(log_router, prefix="/log", tags=["Tool Logging API"])
v1.include_router(chat_router, prefix="/chat", tags=["Chat"])
