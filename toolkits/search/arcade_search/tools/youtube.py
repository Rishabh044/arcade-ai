from typing import Annotated, Any

from arcade.sdk import ToolContext, tool

from arcade_search.utils import call_serpapi, prepare_params


@tool(requires_secrets=["SERP_API_KEY"])
async def search_youtube_videos(
    context: ToolContext,
    keywords: Annotated[
        str,
        "The keywords to search for. For example, ''.",
    ],
) -> Annotated[dict[str, Any], "List of YouTube videos related to the query."]:
    """Search for YouTube videos related to a given query."""
    params = prepare_params("youtube", q=keywords)
    results = call_serpapi(context, params)
    return results
