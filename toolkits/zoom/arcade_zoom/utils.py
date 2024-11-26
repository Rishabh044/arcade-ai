import urllib.parse
from enum import Enum

import httpx

from arcade.sdk import ToolContext

from .constants import ZOOM_BASE_URL


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


async def send_zoom_request(
    context: ToolContext,
    method: HttpMethod,
    endpoint: str,
    params: dict | None = None,
    json_data: dict | None = None,
) -> httpx.Response:
    """
    Send an asynchronous request to the Zoom Meetings API.

    Args:
        context: The tool context containing the authorization token.
        method: The HTTP method (GET, POST, PUT, DELETE, etc.).
        endpoint: The API endpoint path (e.g., "/users/me/upcoming_meetings").
        params: Query parameters to include in the request.
        json_data: JSON data to include in the request body.

    Returns:
        The response object from the API request.
    """
    url = f"{ZOOM_BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {context.authorization.token}"}

    async with httpx.AsyncClient() as client:
        response = await client.request(
            method.value, url, headers=headers, params=params, json=json_data
        )

    return response


def double_encode_uuid(uuid: str) -> str:
    if uuid.startswith("/") or "//" in uuid:
        uuid = urllib.parse.quote(uuid, safe="")
        uuid = urllib.parse.quote(uuid, safe="")
    return uuid
