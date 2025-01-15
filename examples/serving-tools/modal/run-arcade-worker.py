import os

from modal import App, Image, asgi_app

# Define the FastAPI app
app = App("arcade-worker")

toolkits = ["arcade-google", "arcade-slack"]

image = (
    Image.debian_slim()
    .pip_install("arcade-ai[fastapi]")
    .pip_install(toolkits)
    .pip_install("fastapi>=0.110.0")
    .pip_install("uvicorn>=0.24.0")
)


@app.function(image=image)
@asgi_app()
def fastapi_app():
    from fastapi import FastAPI

    from arcade.actor.fastapi.actor import FastAPIActor
    from arcade.core.toolkit import Toolkit

    web_app = FastAPI()

    # Initialize app and Arcade FastAPIActor
    actor_secret = os.environ.get("ARCADE_ACTOR_SECRET", "dev")
    actor = FastAPIActor(web_app, secret=actor_secret)

    # Register toolkits we've installed
    installed_toolkits = Toolkit.find_all_arcade_toolkits()
    for toolkit in toolkits:
        if toolkit in installed_toolkits:
            actor.register_toolkit(toolkit)

    return web_app
