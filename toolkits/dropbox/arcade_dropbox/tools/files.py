from typing import Annotated, Optional

from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import Dropbox
from arcade.sdk.errors import ToolExecutionError

from arcade_dropbox.enums import Endpoint
from arcade_dropbox.utils import send_dropbox_request


@tool(
    requires_auth=Dropbox(
        scopes=["files.content.read"],
    )
)
async def download_file(
    context: ToolContext,
    file_path: Annotated[
        Optional[str],
        "The path to the file to get the contents of. E.g. '/AcmeInc/Reports/Q1_2025.txt'. "
        "Defaults to None.",
    ] = None,
    file_id: Annotated[
        Optional[str],
        "The ID of the file to get the contents of. E.g. 'id:a4ayc_80_OEAAAAAAAAAYa'. "
        "Defaults to None.",
    ] = None,
) -> Annotated[dict, "Contents of the specified file"]:
    """Downloads the specified file.

    Note: either one of `file_path` or `file_id` must be provided.
    """
    if not file_path and not file_id:
        raise ToolExecutionError("Either `file_path` or `file_id` must be provided.")

    if file_path and file_id:
        raise ToolExecutionError("Only one of `file_path` or `file_id` can be provided.")

    result = await send_dropbox_request(
        None if not context.authorization else context.authorization.token,
        endpoint=Endpoint.DOWNLOAD_FILE,
        path=file_path or file_id,
    )

    return {
        "file": result,
    }
