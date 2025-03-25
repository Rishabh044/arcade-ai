from typing import Annotated, Optional

from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import Dropbox

from arcade_dropbox.enums import DropboxEndpoint
from arcade_dropbox.utils import clean_dropbox_entries, send_dropbox_request


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
    next_page_token: Annotated[
        Optional[str],
        "The token for the next page of results. Defaults to None (first page of results).",
    ] = None,
) -> Annotated[dict, "List of files and folders in the specified folder path"]:
    """Returns a list of files and folders in the specified folder path."""
    limit = min(limit, 2000)

    endpoint = (
        DropboxEndpoint.LIST_FOLDER if not next_page_token else DropboxEndpoint.LIST_FOLDER_CONTINUE
    )

    result = await send_dropbox_request(
        context.authorization.token,
        endpoint,
        path=folder_path,
        limit=limit,
        cursor=next_page_token,
    )

    return {
        "items": clean_dropbox_entries(result["entries"]),
        "next_page_token": result.get("cursor"),
        "has_more": result.get("has_more", False),
    }
