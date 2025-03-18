import re
from typing import Any, Optional

import serpapi
from arcade.sdk import ToolContext
from arcade.sdk.errors import ToolExecutionError


# ------------------------------------------------------------------------------------------------
# General SerpAPI utils
# ------------------------------------------------------------------------------------------------
def prepare_params(engine: str, **kwargs: Any) -> dict[str, Any]:
    """
    Prepares a parameters dictionary for the SerpAPI call.

    Parameters:
        engine: The engine name (e.g., "google", "google_finance").
        kwargs: Any additional parameters to include.

    Returns:
        A dictionary containing the base parameters plus any extras,
        excluding any parameters whose value is None.
    """
    params = {"engine": engine}
    params.update({k: v for k, v in kwargs.items() if v is not None})
    return params


def call_serpapi(context: ToolContext, params: dict) -> dict:
    """
    Execute a search query using the SerpAPI client and return the results as a dictionary.

    Args:
        context: The tool context containing required secrets.
        params: A dictionary of parameters for the SerpAPI search.

    Returns:
        The search results as a dictionary.
    """
    api_key = context.get_secret("SERP_API_KEY")
    client = serpapi.Client(api_key=api_key)
    try:
        search = client.search(params)
        return search.as_dict()  # type: ignore[no-any-return]
    except Exception as e:
        # SerpAPI error messages sometimes contain the API key, so we need to sanitize it
        sanitized_e = re.sub(r"(api_key=)[^ &]+", r"\1***", str(e))
        raise ToolExecutionError(
            message="Failed to fetch search results",
            developer_message=sanitized_e,
        )


# ------------------------------------------------------------------------------------------------
# Google Flights utils
# ------------------------------------------------------------------------------------------------
def parse_flight_results(results: dict[str, Any]) -> dict[str, Any]:
    """Parse the flight results from the Google Flights API

    Note: Best flights is not always returned from the API.
    """
    flight_data = {}
    flights = []

    if "best_flights" in results:
        flights.extend(results["best_flights"])
    if "other_flights" in results:
        flights.extend(results["other_flights"])
    if "price_insights" in results:
        flight_data["price_insights"] = results["price_insights"]

    flight_data["flights"] = flights

    return flight_data


# ------------------------------------------------------------------------------------------------
# Google News utils
# ------------------------------------------------------------------------------------------------
def extract_news_results(
    results: dict[str, Any], limit: Optional[int] = None
) -> list[dict[str, Any]]:
    news_results = []
    for result in results.get("news_results", []):
        news_results.append({
            "title": result.get("title"),
            "snippet": result.get("snippet"),
            "link": result.get("link"),
            "date": result.get("date"),
            "source": result.get("source", {}).get("name"),
        })

    if limit:
        return news_results[:limit]
    return news_results
