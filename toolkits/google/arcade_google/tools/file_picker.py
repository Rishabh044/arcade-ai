from urllib.parse import quote_plus

from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import Google


@tool(requires_auth=Google(scopes=["https://www.googleapis.com/auth/drive.file"]))
def file_picker(context: ToolContext):
    """
    Google.PickFiles tool that returns a URL to the /drive_picker endpoint.
    It passes the user's Google token and client ID as query parameters.
    """
    token = context.get_auth_token_or_empty()

    # TODO: Somehow determine the base URL. Probably need to template this similar to the client_id.
    base_url = "https://cloud.arcade.dev"

    oauth_token_enc = quote_plus(token)
    # formatted placeholder for client_id. How does this work for direct tool calling?
    query_params = f"oauth_token={oauth_token_enc}&client_id={{client_id}}"

    # Construct the full URL to the drive_picker endpoint.
    full_url = f"{base_url}/drive_picker?{query_params}"
    return full_url


# a = file_picker(ctx)
# a = a.format(client_id="my-value")
# print(a)
