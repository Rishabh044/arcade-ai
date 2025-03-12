from datetime import datetime, timezone
from typing import Any, Optional

from arcade_search.models import GoogleMapsTravelMode


def google_maps_travel_mode_to_serpapi(travel_mode: GoogleMapsTravelMode) -> int:
    data = {
        GoogleMapsTravelMode.BEST: 6,
        GoogleMapsTravelMode.DRIVING: 0,
        GoogleMapsTravelMode.TWO_WHEELER: 9,
        GoogleMapsTravelMode.TRANSIT: 3,
        GoogleMapsTravelMode.WALKING: 2,
        GoogleMapsTravelMode.CYCLING: 1,
        GoogleMapsTravelMode.FLIGHT: 4,
    }
    return data[travel_mode]


def enrich_google_maps_arrive_around(timestamp: Optional[int]) -> dict[str, Any]:
    if not timestamp:
        return {}

    dt = datetime.fromtimestamp(timestamp).replace(tzinfo=timezone.utc).isoformat()
    return {"datetime": dt, "timestamp": timestamp}
