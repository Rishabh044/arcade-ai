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
async def list_files(
    context: ToolContext,
    path: Annotated[
        str,
        "The path to the folder to list the contents of. "
        "Defaults to an empty string (list items in the root folder).",
    ] = "",
    next_page_token: Annotated[
        Optional[str],
        "The token for the next page of results. Defaults to None (first page of results).",
    ] = None,
) -> Annotated[dict, "List of files in the folder"]:
    """Returns a list of items in the folder."""
    endpoint = (
        DropboxEndpoint.LIST_FOLDER if not next_page_token else DropboxEndpoint.LIST_FOLDER_CONTINUE
    )

    result = await send_dropbox_request(
        context.authorization.token,
        endpoint,
        path=path,
        cursor=next_page_token,
    )

    return {"items": clean_dropbox_entries(result["entries"])}
