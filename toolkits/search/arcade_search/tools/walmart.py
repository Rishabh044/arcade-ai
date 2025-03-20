from typing import Annotated, Any, Optional

from arcade.sdk import ToolContext
from arcade.sdk.errors import ToolExecutionError
from arcade.sdk.tool import tool

from arcade_search.enums import WalmartSortBy
from arcade_search.utils import (
    call_serpapi,
    extract_walmart_results,
    get_walmart_total_pages,
    prepare_params,
)


@tool(requires_secrets=["SERP_API_KEY"])
async def search_walmart_products(
    context: ToolContext,
    keywords: Annotated[str, "Keywords to search for. E.g. 'apple iphone' or 'samsung galaxy'"],
    sort_by: Annotated[
        WalmartSortBy,
        "Sort the results by the specified criteria. "
        f"Defaults to '{WalmartSortBy.RELEVANCE.value}'.",
    ] = WalmartSortBy.RELEVANCE,
    min_price: Annotated[
        Optional[float],
        "Minimum price to filter the results by. E.g. 100.00",
    ] = None,
    max_price: Annotated[
        Optional[float],
        "Maximum price to filter the results by. E.g. 100.00",
    ] = None,
    next_day_delivery: Annotated[
        bool,
        "Filters products that are eligible for next day delivery. "
        "Defaults to False (returns all products, regardless of delivery status).",
    ] = False,
    page: Annotated[
        int,
        "Page number to fetch. Defaults to 1 (first page of results). "
        "The maximum page value is 100.",
    ] = 1,
) -> Annotated[dict[str, Any], "List of Walmart products matching the search query."]:
    """Search Walmart products using SerpAPI."""
    if page > 100:
        raise ToolExecutionError(f"The maximum page value for Walmart search is 100, got {page}.")

    sort_by_value = sort_by.to_api_value()

    params = prepare_params(
        "walmart",
        query=keywords,
        sort=sort_by_value,
        # When the user selects a sorting option, we have to disable the relevance sorting
        # using the soft_sort parameter.
        soft_sort=not sort_by_value,
        min_price=min_price,
        max_price=max_price,
        nd_en=next_day_delivery,
        page=page,
        include_filters=False,
    )

    response = call_serpapi(context, params)

    return {
        "products": extract_walmart_results(response.get("organic_results", [])),
        "current_page": page,
        "total_pages": get_walmart_total_pages(response),
    }
