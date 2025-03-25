from typing import Any, Optional

import httpx

from arcade_dropbox.constants import DROPBOX_API_VERSION, DROPBOX_BASE_URL, DROPBOX_ENDPOINT_URL_MAP
from arcade_dropbox.enums import DropboxEndpoint


def build_dropbox_url(endpoint: DropboxEndpoint) -> str:
    return (
        f"{DROPBOX_BASE_URL}/{DROPBOX_API_VERSION}/{DROPBOX_ENDPOINT_URL_MAP[endpoint].strip('/')}"
    )


def build_dropbox_headers(token: Optional[str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def build_dropbox_json(**kwargs: Any) -> dict:
    return {key: value for key, value in kwargs.items() if value is not None}


async def send_dropbox_request(
    authorization_token: Optional[str],
    endpoint: DropboxEndpoint,
    **kwargs: Any,
) -> Any:
    url = build_dropbox_url(endpoint)
    headers = build_dropbox_headers(authorization_token)
    json = build_dropbox_json(**kwargs)

    if "cursor" in json:
        url += "/continue"

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=json)
        response.raise_for_status()
        return response.json()


def clean_dropbox_entry(entry: dict) -> dict:
    return {
        "type": entry.get(".tag"),
        "id": entry.get("id"),
        "name": entry.get("name"),
        "path": entry.get("path_display"),
        "size": entry.get("size"),
        "modified_time": entry.get("server_modified"),
    }


def clean_dropbox_entries(entries: list[dict]) -> list[dict]:
    return [clean_dropbox_entry(entry) for entry in entries]
