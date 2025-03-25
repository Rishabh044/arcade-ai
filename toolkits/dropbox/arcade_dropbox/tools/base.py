import json
from typing import Annotated, Any, Optional

import httpx
from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import Dropbox
from arcade.sdk.errors import RetryableToolError

# Dropbox API base URLs
DROPBOX_API_URL = "https://api.dropboxapi.com/2"
DROPBOX_CONTENT_URL = "https://content.dropboxapi.com/2"


@tool(requires_auth=Dropbox(scopes=["files.metadata.read"]))
def search_files(
    context: ToolContext,
    query: Annotated[str, "Filename query to search for."],
    folder_path: Annotated[
        str, "Folder path to start the search from. Defaults to root folder."
    ] = "/",
) -> list[dict[str, Any]]:
    """
    Search for files in Dropbox matching the given filename query.
    This tool uses the Dropbox API's /files/search_v2 endpoint with recursive search.
    It returns a list of metadata dictionaries for files that match the query.
    """
    url = f"{DROPBOX_API_URL}/files/search_v2"
    headers = {
        "Authorization": f"Bearer {context.get_auth_token_or_empty()}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "options": {
            "path": folder_path,
            "max_results": 100,
            "filename_only": True,
            "file_status": "active",
        },
    }

    try:
        response = httpx.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        matches = data.get("matches", [])
        results = []
        for match in matches:
            # The metadata is nested under "metadata" twice in search_v2 responses.
            metadata = match.get("metadata", {}).get("metadata", {})
            results.append(metadata)
        return results  # noqa: TRY300
    except Exception as e:
        msg = f"Error in searching files: {e}"
        raise RetryableToolError(
            msg,
            retry_after_ms=500,
            developer_message="Dropbox API error searching files",
        ) from e


@tool(requires_auth=Dropbox(scopes=["files.metadata.read"]))
def list_folder_contents(
    context: ToolContext,
    folder_path: Annotated[str, "The Dropbox folder path to list contents from."],
    filetype: Annotated[
        Optional[str], "Optional file extension to filter by (e.g., '.txt')"
    ] = None,
) -> list[dict[str, Any]]:
    """
    List all contents within a folder (recursively) from Dropbox using the /files/list_folder endpoint.
    Optionally, the result is filtered by file extension.
    Returns a list of metadata dictionaries.
    """
    url = f"{DROPBOX_API_URL}/files/list_folder"
    headers = {
        "Authorization": f"Bearer {context.get_auth_token_or_empty()}",
        "Content-Type": "application/json",
    }
    payload = {"path": folder_path, "recursive": True}
    results = []
    try:
        response = httpx.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        results.extend(data.get("entries", []))
        # Continue paging if there are more entries.
        while data.get("has_more", False):
            cursor = data.get("cursor")
            list_continue_url = f"{DROPBOX_API_URL}/files/list_folder/continue"
            response = httpx.post(list_continue_url, headers=headers, json={"cursor": cursor})
            response.raise_for_status()
            data = response.json()
            results.extend(data.get("entries", []))
        # If filetype filter is provided, filter the list.
        if filetype:
            results = [
                entry
                for entry in results
                if entry.get(".tag") == "file"
                and entry.get("name", "").lower().endswith(filetype.lower())
            ]
        return results  # noqa: TRY300
    except Exception as e:
        msg = f"Error listing folder contents: {e}"
        raise RetryableToolError(
            msg,
            retry_after_ms=500,
            developer_message="Dropbox API error listing folder contents",
        ) from e


@tool(requires_auth=Dropbox(scopes=["files.content.read"]))
def download_file(
    context: ToolContext, file_path: Annotated[str, "The Dropbox path of the file to download."]
) -> str:
    """
    Download a file's content from Dropbox using the /files/download endpoint.
    Returns the file content as a string.
    """
    url = f"{DROPBOX_CONTENT_URL}/files/download"
    headers = {
        "Authorization": f"Bearer {context.get_auth_token_or_empty()}",
        "Dropbox-API-Arg": json.dumps({"path": file_path}),
    }
    try:
        response = httpx.post(url, headers=headers)
        response.raise_for_status()
        # The file content is returned in the response body.
        return response.text  # noqa: TRY300
    except Exception as e:
        msg = f"Error downloading file: {e}"
        raise RetryableToolError(
            msg,
            retry_after_ms=500,
            developer_message="Dropbox API error downloading file",
        ) from e


@tool(requires_auth=Dropbox(scopes=["files.content.write"]))
def update_file_contents(
    context: ToolContext,
    file_path: Annotated[str, "The Dropbox path of the file to update."],
    content: Annotated[str, "The new content to write into the file."],
) -> str:
    """
    Update (overwrite) a file in Dropbox with new content using the /files/upload endpoint.
    The new content is uploaded with the 'overwrite' mode.
    Returns a message indicating the update was successful.
    """
    url = f"{DROPBOX_CONTENT_URL}/files/upload"
    headers = {
        "Authorization": f"Bearer {context.get_auth_token_or_empty()}",
        "Content-Type": "application/octet-stream",
        "Dropbox-API-Arg": json.dumps({
            "path": file_path,
            "mode": "overwrite",
            "autorename": False,
            "mute": True,
        }),
    }
    try:
        # Dropbox expects file content in binary form.
        response = httpx.post(url, headers=headers, content=content.encode("utf-8"))
        response.raise_for_status()
        data = response.json()
        return f"File '{data.get('name')}' updated successfully."
    except Exception as e:
        msg = f"Error updating file: {e}"
        raise RetryableToolError(
            msg,
            retry_after_ms=500,
            developer_message="Dropbox API error updating file",
        ) from e
