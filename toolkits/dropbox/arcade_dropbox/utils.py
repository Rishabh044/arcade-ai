import json
from typing import Any, Optional

import httpx
from arcade.sdk.errors import ToolExecutionError

from arcade_dropbox.constants import (
    API_BASE_URL,
    API_VERSION,
    ENDPOINT_URL_MAP,
)
from arcade_dropbox.enums import Endpoint, EndpointType
from arcade_dropbox.exceptions import DropboxPathNotFoundError


def build_dropbox_url(endpoint_type: EndpointType, endpoint_path: str) -> str:
    base_url = API_BASE_URL.format(endpoint_type=endpoint_type.value)
    return f"{base_url}/{API_VERSION}/{endpoint_path.strip('/')}"


def build_dropbox_headers(token: Optional[str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def build_dropbox_json(**kwargs: Any) -> dict:
    return {key: value for key, value in kwargs.items() if value is not None}


async def send_dropbox_request(
    authorization_token: Optional[str],
    endpoint: Endpoint,
    **kwargs: Any,
) -> Any:
    endpoint_type, endpoint_path = ENDPOINT_URL_MAP[endpoint]
    url = build_dropbox_url(endpoint_type, endpoint_path)
    headers = build_dropbox_headers(authorization_token)
    json_data = build_dropbox_json(**kwargs)

    if "cursor" in json_data:
        url += "/continue"

    if endpoint_type == EndpointType.CONTENT:
        headers["Dropbox-API-Arg"] = json.dumps(json_data)
        json_data = None

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=json_data)

        try:
            data = response.json()
        except Exception:
            data = {}

        if response.status_code == 409 and "path/not_found" in data.get("error_summary", ""):
            raise DropboxPathNotFoundError()

        if response.status_code != 200:
            message = (
                f"Dropbox request failed with status code {response.status_code} "
                f"and response: {response.text}"
            )
            raise ToolExecutionError(message)

        if endpoint_type == EndpointType.CONTENT:
            data = json.loads(response.headers["Dropbox-API-Result"])
            data = clean_dropbox_entry(data, default_type="file")
            data["content"] = response.text
            return data

        return response.json()


def clean_dropbox_entry(entry: dict, default_type: Optional[str] = None) -> dict:
    return {
        "type": entry.get(".tag", default_type),
        "id": entry.get("id"),
        "name": entry.get("name"),
        "path": entry.get("path_display"),
        "size_in_bytes": entry.get("size"),
        "modified_datetime": entry.get("server_modified"),
    }


def clean_dropbox_entries(entries: list[dict]) -> list[dict]:
    return [clean_dropbox_entry(entry) for entry in entries]


def parse_dropbox_path(path: Optional[str]) -> Optional[str]:
    if not isinstance(path, str):
        return None

    if not path:
        return ""

    # Dropbox expects the path to always start with a slash
    return "/" + path.strip("/")
