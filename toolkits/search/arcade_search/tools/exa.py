from typing import Annotated, Optional

from exa_py import Exa

from arcade.sdk import tool
from arcade.sdk.errors import RetryableToolError
from arcade_search.tools.models import SearchType
from arcade_search.tools.utils import get_secret


@tool
async def search_exa(
    query: Annotated[str, "Search query"],
    search_type: Annotated[
        str,
        "Neural uses embeddings. Keyword uses traditional search. Auto decides between neural and keyword, based on the query.",
    ] = SearchType.AUTO,
    use_autoprompt: Annotated[
        Optional[bool],
        "If true, the provided query will be converted to a prompt-engineered Exa query.",
    ] = False,
    num_results: Annotated[int, "Number of results to retrieve"] = 10,
) -> Annotated[str, "Search results as a string"]:
    """Perform a web search.
    The search uses 'exa' to retrieve a list of relevant results without the webpage contents.
    Requires EXA_API_KEY to be set.
    """

    api_key = get_secret("EXA_API_KEY")
    if not api_key:
        raise ValueError("EXA_API_KEY is not set")

    exa = Exa(api_key=api_key)
    result = exa.search(
        query,
        type=search_type,
        use_autoprompt=use_autoprompt,
        num_results=num_results,
    )

    return str(result)


@tool
async def search_and_contents_exa(
    query: Annotated[str, "Search query"],
    search_type: Annotated[
        str,
        "Neural uses embeddings. Keyword uses traditional search. Auto decides between neural and keyword, based on the query.",
    ] = SearchType.AUTO,
    use_autoprompt: Annotated[
        Optional[bool],
        "If true, the provided query will be converted to a prompt-engineered Exa query.",
    ] = False,
    num_results: Annotated[int, "Number of results to retrieve"] = 10,
) -> Annotated[str, "Search results as a string"]:
    """Perform a search and get the contents of the results.
    The search uses a 'exa' to retrieve a list of relevant results with the webpage contents for each result.
    Requires EXA_API_KEY to be set.
    """

    api_key = get_secret("EXA_API_KEY")
    if not api_key:
        raise ValueError("EXA_API_KEY is not set")

    exa = Exa(api_key=api_key)
    result = exa.search_and_contents(
        query,
        type=search_type,
        use_autoprompt=use_autoprompt,
        num_results=num_results,
        text=True,
    )

    return str(result)


@tool
async def find_similar_exa(
    url: Annotated[str, "URL of the page to find similar results for"],
    num_results: Annotated[int, "Number of results to retrieve"] = 10,
    exclude_source_domain: Annotated[
        Optional[bool], "Whether to exclude the source domain from the results"
    ] = False,
) -> Annotated[str, "Search results as a string"]:
    """Find similar results for a given URL.
    Uses 'exa'' API.
    Requires EXA_API_KEY to be set.
    """
    print("URL HERE: ", url)

    api_key = get_secret("EXA_API_KEY")
    if not api_key:
        raise ValueError("EXA_API_KEY is not set")

    exa = Exa(api_key=api_key)
    try:
        result = exa.find_similar(
            url,
            num_results=num_results,
            exclude_source_domain=exclude_source_domain,
        )
    except ValueError as e:
        additional_prompt_content = f"{url} is not a valid URL."
        raise RetryableToolError(
            additional_prompt_content + str(e),
            additional_prompt_content=additional_prompt_content,
            retry_after_ms=500,
        )

    return str(result)


@tool
async def find_similar_and_contents_exa(
    url: Annotated[str, "URL of the page to find similar results for"],
    num_results: Annotated[int, "Number of results to retrieve"] = 10,
    exclude_source_domain: Annotated[
        Optional[bool], "Whether to exclude the source domain from the results"
    ] = False,
) -> Annotated[str, "Search results as a string"]:
    """Find similar results for a given URL.
    Uses 'exa' API and retrieves the contents of the results.
    Requires EXA_API_KEY to be set.
    """

    api_key = get_secret("EXA_API_KEY")
    if not api_key:
        raise ValueError("EXA_API_KEY is not set")

    exa = Exa(api_key=api_key)
    try:
        result = exa.find_similar_and_contents(
            url,
            num_results=num_results,
            exclude_source_domain=exclude_source_domain,
            text=True,
            highlights=True,
        )
    except ValueError as e:
        additional_prompt_content = f"{url} is not a valid URL."
        raise RetryableToolError(
            additional_prompt_content + str(e),
            additional_prompt_content=additional_prompt_content,
            retry_after_ms=500,
        )

    return str(result)
