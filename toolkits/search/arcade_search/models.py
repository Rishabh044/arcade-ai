import enum


class GoogleMapsTravelMode(enum.Enum):
    BEST = "best"
    DRIVING = "driving"
    MOTORCYCLE = "two_wheel"
    TRANSIT = "transit"
    WALKING = "walking"
    CYCLING = "cycling"
    FLIGHT = "flight"


class GoogleMapsDistanceUnit(enum.Enum):
    KM = "km"
    MILES = "mi"
