import os
from enum import Enum
from typing import Annotated, Any, Optional

from exa_py import Exa

from arcade.sdk import tool
from arcade.sdk.errors import RetryableToolError


class SearchType(str, Enum):
    NEURAL = "neural"  # Uses embeddings
    KEYWORD = "keyword"  # Uses traditional search
    AUTO = "auto"  # Decides betwee neural and keyword, based on the query


@tool
async def search_exa(
    query: Annotated[str, "Search query"],
    search_type: Annotated[
        str,
        "Neural uses embeddings. Keyword uses traditional search. Auto decides between neural and keyword, based on the query.",
    ] = SearchType.NEURAL,
    use_autoprompt: Annotated[Optional[bool], ""] = True,
    num_results: Annotated[int, "Number of results to retrieve"] = 10,
) -> Annotated[str, "Search results as a string"]:
    """
    Perform a search with a Exa prompt-engineered query and retrieve a list of relevant results.
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
    ] = SearchType.NEURAL,
    use_autoprompt: Annotated[Optional[bool], ""] = True,
    num_results: Annotated[int, "Number of results to retrieve"] = 10,
) -> Annotated[str, "Search results as a string"]:
    """
    Perform a search with a Exa prompt-engineered query and retrieve a list of relevant results with the webpage contents for each result.
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
    """
    Find similar results for a given URL using Exa API.
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
    """
    Find similar results for a given URL using Exa API and retrieve the contents of the results.
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


def get_secret(name: str, default: Optional[Any] = None) -> Any:
    secret = os.getenv(name)
    if secret is None:
        if default is not None:
            return default
        raise ValueError(f"Secret {name} is not set.")
    return secret
