import json
from typing import Any, Optional

import httpx

from arcade_dropbox.constants import (
    API_BASE_URL,
    API_VERSION,
    ENDPOINT_URL_MAP,
    Endpoint,
    EndpointType,
)
from arcade_dropbox.exceptions import DropboxApiError


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

    if json_data.get("cursor"):
        url += "/continue"
        # If cursor is provided, every other argument must be ignored to avoid API error
        json_data = {"cursor": json_data["cursor"]}

    if endpoint_type == EndpointType.CONTENT:
        headers["Dropbox-API-Arg"] = json.dumps(json_data)
        json_data = {}

    async with httpx.AsyncClient() as client:
        request_args: dict[str, Any] = {"url": url, "headers": headers}

        if json_data:
            request_args["json"] = json_data

        response = await client.post(**request_args)

        try:
            data = response.json()
        except Exception:
            data = {}

        if response.status_code != 200:
            raise DropboxApiError(
                status_code=response.status_code,
                error_summary=data.get("error_summary", response.text),
                user_message=data.get("user_message"),
            )

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
        return ""

    if not path:
        return ""

    if path in ["/", "\\"]:
        return ""

    # Normalize windows-style paths to unix-style paths
    path = path.replace("\\", "/")

    # Dropbox expects the path to always start with a slash
    return "/" + path.strip("/")
