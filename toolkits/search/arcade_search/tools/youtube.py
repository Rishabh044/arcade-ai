from typing import Annotated, Any, Optional

from arcade.sdk import ToolContext, tool

from arcade_search.constants import DEFAULT_YOUTUBE_SEARCH_COUNTRY, DEFAULT_YOUTUBE_SEARCH_LANGUAGE
from arcade_search.exceptions import CountryNotFoundError, LanguageNotFoundError
from arcade_search.google_data import COUNTRY_CODES, LANGUAGE_CODES
from arcade_search.utils import call_serpapi, prepare_params


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
        "Defaults to `None` (no language filters).",
    ] = None,
    country_code: Annotated[
        Optional[str],
        "2-character country code to search for. E.g. 'us' for United States. "
        "Defaults to `None` (no country filters).",
    ] = None,
    next_page_token: Annotated[
        Optional[str],
        "The next page token to use for pagination. "
        "Defaults to `None` (start from the first page).",
    ] = None,
) -> Annotated[dict[str, Any], "List of YouTube videos related to the query."]:
    if language_code is None and DEFAULT_YOUTUBE_SEARCH_LANGUAGE:
        language_code = DEFAULT_YOUTUBE_SEARCH_LANGUAGE
    if country_code is None and DEFAULT_YOUTUBE_SEARCH_COUNTRY:
        country_code = DEFAULT_YOUTUBE_SEARCH_COUNTRY

    if language_code and language_code not in LANGUAGE_CODES:
        raise LanguageNotFoundError(language_code)
    if country_code and country_code not in COUNTRY_CODES:
        raise CountryNotFoundError(country_code)

    params = prepare_params(
        "youtube",
        q=keywords,
        hl=language_code,
        gl=country_code,
        sp=next_page_token,
    )
    results = call_serpapi(context, params)
    return results
