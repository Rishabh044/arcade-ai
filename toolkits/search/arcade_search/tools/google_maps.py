import json
from typing import Annotated, Optional

import serpapi
from arcade.core.errors import RetryableToolError
from arcade.sdk import ToolContext, tool

from arcade_search.google_maps_data import COUNTRY_CODES, LANGUAGE_CODES
from arcade_search.models import GoogleMapsDistanceUnit, GoogleMapsTravelMode
from arcade_search.utils import enrich_google_maps_arrive_around, google_maps_travel_mode_to_serpapi


@tool(requires_secrets=["SERP_API_KEY"])
async def get_directions_by_address(
    context: ToolContext,
    origin: Annotated[str, "The origin location or address"],
    destination: Annotated[str, "The destination location or address"],
    language: Annotated[
        str, "Language to use in the Google Maps search. Defaults to 'en' (English)."
    ] = "en",
    country: Annotated[
        Optional[str],
        "2-letter country code to use in the Google Maps search. Defaults to None "
        "(no country is specified).",
    ] = None,
    distance_unit: Annotated[
        GoogleMapsDistanceUnit,
        "Distance unit to use in the Google Maps search. Defaults to 'km' (kilometers).",
    ] = GoogleMapsDistanceUnit.KM,
    travel_mode: Annotated[
        GoogleMapsTravelMode,
        "Travel mode to use in the Google Maps search. Defaults to 'best' (best mode).",
    ] = GoogleMapsTravelMode.BEST,
) -> str:
    """Get directions from Google Maps."""

    if language not in LANGUAGE_CODES:
        raise RetryableToolError(
            f"Invalid language: {language}",
            additional_prompt_content=f"Valid languages are: {json.dumps(LANGUAGE_CODES)}",
        )

    api_key = context.get_secret("SERP_API_KEY")

    client = serpapi.Client(api_key=api_key)
    params = {
        "engine": "google_maps",
        "start_addr": origin,
        "end_addr": destination,
        "hl": language,
        "distance_unit": distance_unit.value,
        "travel_mode": google_maps_travel_mode_to_serpapi(travel_mode),
    }

    if country:
        if country not in COUNTRY_CODES:
            raise RetryableToolError(
                f"Invalid country: {country}",
                additional_prompt_content=f"Valid countries are: {json.dumps(COUNTRY_CODES)}",
            )
        params["gl"] = country

    search = client.search(params)
    results = search.as_dict()

    for direction in results["directions"]:
        direction["arrive_around"] = enrich_google_maps_arrive_around(direction["arrive_time"])

    return json.dumps(results)


@tool(requires_secrets=["SERP_API_KEY"])
async def get_directions_by_coordinates(
    context: ToolContext,
    origin_latitude: Annotated[float, "The origin latitude"],
    origin_longitude: Annotated[float, "The origin longitude"],
    destination_latitude: Annotated[float, "The destination latitude"],
    destination_longitude: Annotated[float, "The destination longitude"],
    language: Annotated[
        str, "Language to use in the Google Maps search. Defaults to 'en' (English)."
    ] = "en",
    country: Annotated[
        Optional[str],
        "2-letter country code to use in the Google Maps search. Defaults to None "
        "(no country is specified).",
    ] = None,
    distance_unit: Annotated[
        GoogleMapsDistanceUnit,
        "Distance unit to use in the Google Maps search. Defaults to 'km' (kilometers).",
    ] = GoogleMapsDistanceUnit.KM,
    travel_mode: Annotated[
        GoogleMapsTravelMode,
        "Travel mode to use in the Google Maps search. Defaults to 'best' (best mode).",
    ] = GoogleMapsTravelMode.BEST,
) -> str:
    """Get directions from Google Maps."""

    if language not in LANGUAGE_CODES:
        raise RetryableToolError(
            f"Invalid language: {language}",
            additional_prompt_content=f"Valid languages are: {json.dumps(LANGUAGE_CODES)}",
        )

    api_key = context.get_secret("SERP_API_KEY")

    client = serpapi.Client(api_key=api_key)
    params = {
        "engine": "google_maps",
        "start_coords": f"{origin_latitude},{origin_longitude}",
        "end_coords": f"{destination_latitude},{destination_longitude}",
        "hl": language,
        "distance_unit": distance_unit.value,
        "travel_mode": google_maps_travel_mode_to_serpapi(travel_mode),
    }

    if country:
        if country not in COUNTRY_CODES:
            raise RetryableToolError(
                f"Invalid country: {country}",
                additional_prompt_content=f"Valid countries are: {json.dumps(COUNTRY_CODES)}",
            )
        params["gl"] = country

    search = client.search(params)
    results = search.as_dict()

    for direction in results["directions"]:
        direction["arrive_around"] = enrich_google_maps_arrive_around(direction["arrive_time"])

    return json.dumps(results)
