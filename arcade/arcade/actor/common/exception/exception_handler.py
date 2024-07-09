#!/usr/bin/env python3
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from pydantic.errors import PydanticUserError
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware

from arcade.actor.common.exception.errors import BaseExceptionMixin
from arcade.actor.common.log import log
from arcade.actor.common.response_code import (
    CustomResponseCode,
    StandardResponseCode,
    response_base,
)
from arcade.actor.core.conf import settings
from arcade.actor.schemas.base import (
    CUSTOM_USAGE_ERROR_MESSAGES,
)
from arcade.actor.utils.serializers import MsgSpecJSONResponse


async def _validation_exception_handler(
    request: Request, e: RequestValidationError | ValidationError
):
    """
    Data validation exception handling

    :param e:
    :return:
    """
    error = e.errors()[0]
    if error.get("type") == "json_invalid":
        message = "JSON parsing failed"
    else:
        error_input = error.get("input")
        field = str(error.get("loc")[-1])
        error_msg = error.get("msg")
        message = f"{field} {error_msg}, input: {error_input}"
    msg = f"Invalid request parameters: {message}"
    data = {"errors": error} if settings.ENVIRONMENT == "dev" else None
    content = {
        "code": StandardResponseCode.HTTP_422,
        "msg": msg,
        "data": data,
    }
    request.state.__request_validation_exception__ = (
        content  # For obtaining exception information in middleware
    )
    return MsgSpecJSONResponse(status_code=422, content=content)


def register_exception(app: FastAPI):  # noqa: C901
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        Global HTTP exception handling

        :param request:
        :param exc:
        :return:
        """
        if settings.ENVIRONMENT == "dev":
            content = {
                "code": exc.status_code,
                "msg": exc.detail,
                "data": None,
            }
        else:
            res = await response_base.fail(res=CustomResponseCode.HTTP_400)
            content = res.model_dump()
        request.state.__request_http_exception__ = (
            content  # For obtaining exception information in middleware
        )
        return MsgSpecJSONResponse(
            status_code=StandardResponseCode.HTTP_400,
            content=content,
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def fastapi_validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        FastAPI data validation exception handling

        :param request:
        :param exc:
        :return:
        """
        return await _validation_exception_handler(request, exc)

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
        """
        Pydantic data validation exception handling

        :param request:
        :param exc:
        :return:
        """
        return await _validation_exception_handler(request, exc)

    @app.exception_handler(PydanticUserError)
    async def pydantic_user_error_handler(request: Request, exc: PydanticUserError):
        """
        Pydantic user exception handling

        :param request:
        :param exc:
        :return:
        """
        return MsgSpecJSONResponse(
            status_code=StandardResponseCode.HTTP_500,
            content={
                "code": StandardResponseCode.HTTP_500,
                "msg": CUSTOM_USAGE_ERROR_MESSAGES.get(exc.code),
                "data": None,
            },
        )

    @app.exception_handler(AssertionError)
    async def assertion_error_handler(request: Request, exc: AssertionError):
        """
        Assertion error handling

        :param request:
        :param exc:
        :return:
        """
        if settings.ENVIRONMENT == "dev":
            content = {
                "code": StandardResponseCode.HTTP_500,
                "msg": str("".join(exc.args) if exc.args else exc.__doc__),
                "data": None,
            }
        else:
            res = await response_base.fail(res=CustomResponseCode.HTTP_500)
            content = res.model_dump()
        return MsgSpecJSONResponse(
            status_code=StandardResponseCode.HTTP_500,
            content=content,
        )

    @app.exception_handler(Exception)
    async def all_exception_handler(request: Request, exc: Exception):
        """
        Global exception handling

        :param request:
        :param exc:
        :return:
        """
        if isinstance(exc, BaseExceptionMixin):
            return MsgSpecJSONResponse(
                status_code=StandardResponseCode.HTTP_400,
                content={
                    "code": exc.code,
                    "msg": str(exc.msg),
                    "data": exc.data if exc.data else None,
                },
                background=exc.background,
            )
        else:
            import traceback

            log.error(f"Unknown exception: {exc}")
            log.error(traceback.format_exc())
            if settings.ENVIRONMENT == "dev":
                content = {
                    "code": 500,
                    "msg": str(exc),
                    "data": None,
                }
            else:
                res = await response_base.fail(res=CustomResponseCode.HTTP_500)
                content = res.model_dump()
            return MsgSpecJSONResponse(status_code=StandardResponseCode.HTTP_500, content=content)

    if settings.MIDDLEWARE_CORS:

        @app.exception_handler(StandardResponseCode.HTTP_500)
        async def cors_status_code_500_exception_handler(request, exc):
            """
            CORS 500 exception handling

            `Related issue <https://github.com/encode/starlette/issues/1175>`_

            :param request:
            :param exc:
            :return:
            """
            if isinstance(exc, BaseExceptionMixin):
                content = {
                    "code": exc.code,
                    "msg": exc.msg,
                    "data": exc.data,
                }
            else:
                if settings.ENVIRONMENT == "dev":
                    content = {
                        "code": StandardResponseCode.HTTP_500,
                        "msg": str(exc),
                        "data": None,
                    }
                else:
                    res = await response_base.fail(res=CustomResponseCode.HTTP_500)
                    content = res.model_dump()
            response = MsgSpecJSONResponse(
                status_code=exc.code
                if isinstance(exc, BaseExceptionMixin)
                else StandardResponseCode.HTTP_500,
                content=content,
                background=exc.background if isinstance(exc, BaseExceptionMixin) else None,
            )
            origin = request.headers.get("origin")
            if origin:
                cors = CORSMiddleware(
                    app=app,
                    allow_origins=["*"],
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                )
                response.headers.update(cors.simple_headers)
                has_cookie = "cookie" in request.headers
                if cors.allow_all_origins and has_cookie:
                    response.headers["Access-Control-Allow-Origin"] = origin
                elif not cors.allow_all_origins and cors.is_allowed_origin(origin=origin):
                    response.headers["Access-Control-Allow-Origin"] = origin
                    response.headers.add_vary_header("Origin")
            return response
