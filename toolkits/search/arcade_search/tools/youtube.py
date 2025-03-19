from typing import Annotated, Any, Optional

from arcade.sdk import ToolContext, tool

from arcade_search.constants import DEFAULT_YOUTUBE_SEARCH_COUNTRY, DEFAULT_YOUTUBE_SEARCH_LANGUAGE
from arcade_search.utils import (
    call_serpapi,
    default_country_code,
    default_language_code,
    prepare_params,
    resolve_country_code,
    resolve_language_code,
)


@tool(requires_secrets=["SERP_API_KEY"])
async def search_youtube_videos(
    context: ToolContext,
    keywords: Annotated[
        str,
        "The keywords to search for. E.g. 'Python tutorial'.",
    ],
    language_code: Annotated[
        Optional[str],
        "2-character language code to search for. E.g. 'en' for English. "
        f"Defaults to '{default_language_code(DEFAULT_YOUTUBE_SEARCH_LANGUAGE)}'.",
    ] = None,
    country_code: Annotated[
        Optional[str],
        "2-character country code to search for. E.g. 'us' for United States. "
        f"Defaults to '{default_country_code(DEFAULT_YOUTUBE_SEARCH_COUNTRY)}'.",
    ] = None,
    next_page_token: Annotated[
        Optional[str],
        "The next page token to use for pagination. "
        "Defaults to `None` (start from the first page).",
    ] = None,
) -> Annotated[dict[str, Any], "List of YouTube videos related to the query."]:
    language_code = resolve_language_code(language_code, DEFAULT_YOUTUBE_SEARCH_LANGUAGE)
    country_code = resolve_country_code(country_code, DEFAULT_YOUTUBE_SEARCH_COUNTRY)

    params = prepare_params(
        "youtube",
        q=keywords,
        hl=language_code,
        gl=country_code,
        sp=next_page_token,
    )
    results = call_serpapi(context, params)
    return results
