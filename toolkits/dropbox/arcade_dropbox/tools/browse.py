from typing import Annotated, Optional

from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import Dropbox
from arcade.sdk.errors import ToolExecutionError

from arcade_dropbox.enums import DropboxEndpoint
from arcade_dropbox.utils import build_dropbox_json, clean_dropbox_entries, send_dropbox_request


@tool(
    requires_auth=Dropbox(
        scopes=["files.metadata.read"],
    )
)
async def list_items_in_folder(
    context: ToolContext,
    folder_path: Annotated[
        str,
        "The path to the folder to list the contents of. "
        "Defaults to an empty string (list items in Dropbox root folder).",
    ] = "",
    limit: Annotated[
        int,
        "The maximum number of items to return. Defaults to 100. Maximum allowed is 2000.",
    ] = 100,
    cursor: Annotated[
        Optional[str],
        "The cursor token for the next page of results. Defaults to None (first page of results).",
    ] = None,
) -> Annotated[dict, "List of files and folders in the specified folder path"]:
    """Returns a list of files and folders in the specified folder path."""
    limit = min(limit, 2000)

    result = await send_dropbox_request(
        None if not context.authorization else context.authorization.token,
        endpoint=DropboxEndpoint.LIST_FOLDER,
        path=folder_path,
        limit=limit,
        cursor=cursor,
    )

    return {
        "items": clean_dropbox_entries(result["entries"]),
        "next_page_token": result.get("cursor"),
        "has_more": result.get("has_more", False),
    }


@tool(
    requires_auth=Dropbox(
        scopes=["files.metadata.read"],
    )
)
async def search_items_by_keywords(
    context: ToolContext,
    keywords: Annotated[
        str, "The keywords to search for in the folder. Maximum length is 1000 characters."
    ],
    search_in_folder_path: Annotated[
        str,
        "Restricts the search to the specified folder path. "
        "Defaults to an empty string (search in the entire Dropbox).",
    ] = "",
    limit: Annotated[
        int,
        "The maximum number of items to return. Defaults to 100. Maximum allowed is 1000.",
    ] = 100,
    cursor: Annotated[
        Optional[str],
        "The cursor token for the next page of results. Defaults to None (first page of results).",
    ] = None,
) -> Annotated[dict, "List of items in the specified folder path matching the search criteria"]:
    """Returns a list of items in the specified folder path matching the search criteria.

    Note: the Dropbox API will return up to 10,000 (ten thousand) items cumulatively across multiple
    pagination requests using the cursor token.
    """
    if len(keywords) > 1000:
        raise ToolExecutionError(
            "The keywords argument must be a string with up to 1000 characters."
        )

    limit = min(limit, 1000)

    result = await send_dropbox_request(
        None if not context.authorization else context.authorization.token,
        endpoint=DropboxEndpoint.SEARCH_FILES,
        query=keywords,
        options=build_dropbox_json(
            path=search_in_folder_path,
            max_results=limit,
        ),
        cursor=cursor,
    )

    return {
        "items": result["matches"],
        "next_page_token": result.get("cursor"),
        "has_more": result.get("has_more", False),
    }
