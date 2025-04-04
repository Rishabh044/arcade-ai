from typing import Annotated, Any

from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import OAuth2


@tool(
    requires_auth=OAuth2(
        provider_id="hubspot",
        scopes=["crm.objects.companies.read"],
    ),
)
def search_companies(
    context: ToolContext,
    query: Annotated[str, "The query to search for companies."],
    limit: Annotated[int, "The maximum number of companies to return."],
) -> Annotated[dict[str, Any], "The companies that match the query."]:
    pass
