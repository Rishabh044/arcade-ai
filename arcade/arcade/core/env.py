import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


# https://docs.pydantic.dev/latest/concepts/pydantic_settings/
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    WORK_DIR: Path = Path.home() / ".arcade"
    TOOLS_DIR: Path = Path(os.getcwd())

    # Env Config
    ENVIRONMENT: Literal["dev", "pro"] = "dev"

    # FastAPI
    API_V1_STR: str = "/v1"
    API_ACTION_STR: str = "/tool"
    TITLE: str = "Arcade AI Toolserver"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Arcade AI Toolserver API"
    DOCS_URL: str | None = f"{API_V1_STR}/docs"
    REDOCS_URL: str | None = f"{API_V1_STR}/redocs"
    OPENAPI_URL: str | None = f"{API_V1_STR}/openapi"

    #    @model_validator(mode='before')
    #    @classmethod
    #    def validate_openapi_url(cls, values):
    #        if values['ENVIRONMENT'] == 'pro':
    #            values['OPENAPI_URL'] = None
    #        return values


@lru_cache
def get_settings() -> Settings:
    # TODO allow user to specify env file path as a Env Var
    return Settings()


settings = get_settings()
