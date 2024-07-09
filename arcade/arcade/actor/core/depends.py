from starlette.requests import Request


def get_catalog(request: Request):
    return request.app.state.catalog
