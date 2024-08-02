import asyncio
from typing import Any, Callable
import functools

from fastapi import Depends, FastAPI, Request

from arcade.actor.core.base import BaseActor
from pydantic import BaseModel


class FastAPIActor(BaseActor):
    def __init__(self, app: FastAPI) -> None:
        """
        Initialize the FastAPIActor with a FastAPI app
        instance and an empty ToolCatalog.
        """
        super().__init__()
        self.app = app
        self.router = FastAPIRouter(app, self)
        self.register_routes(self.router)


class FastAPIRouter:  # TODO create an interface for this
    def __init__(self, app: FastAPI, actor: BaseActor) -> None:
        self.app = app
        self.actor = actor

    def add_route(
        self,
        path: str,
        handler: Callable,
        methods: str,
        description: str,
        response_model: Any,
        name: str,
        input_model: BaseModel = None,
    ) -> None:
        """
        Add a route to the FastAPI application.
        """

        dependencies = []
        if input_model:
            dependencies.append(Depends(input_model))

        self.app.add_api_route(
            path,
            self.wrap_handler(handler),
            methods=methods,
            description=description,
            response_model=response_model,
            name=name,
            dependencies=dependencies,
        )
        # for method in methods:
        #     if method == "GET":
        #         self.app.add_api_route(path,
        #         #self.app.get(path)(self.wrap_handler(handler))
        #     elif method == "POST":
        #         self.app.post(path)(self.wrap_handler(handler))
        #     elif method == "PUT":
        #         self.app.put(path)(self.wrap_handler(handler))
        #     elif method == "DELETE":
        #         self.app.delete(path)(self.wrap_handler(handler))
        #     else:
        #         raise ValueError(f"Unsupported HTTP method: {method}")

    def wrap_handler(self, handler: Callable) -> Callable:
        """
        Wrap the handler to handle FastAPI-specific request and response.
        """

        # @functools.wraps(handler)
        async def wrapped_handler(
            request: Request,
            # api_key: str = Depends(get_api_key), # TODO re-enable when Engine supports auth
        ) -> Any:
            if asyncio.iscoroutinefunction(handler) or (
                callable(handler) and asyncio.iscoroutinefunction(handler.__call__)  # type: ignore[operator]
            ):
                return await handler(request)
            else:
                return handler(request)

        return wrapped_handler
