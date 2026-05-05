import logging
from datetime import datetime, timedelta
from typing import List

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.Pozi import PoziGeoJsonError, query_geojson_zones

TITLE = "City of Greater Bendigo"
DESCRIPTION = "Source for City of Greater Bendigo rubbish collection."
URL = "https://www.bendigo.vic.gov.au"

# Geographic boundaries for Bendigo area
BENDIGO_BOUNDS = {
    "min_lat": -37.07,
    "min_lon": 144.03,
    "max_lat": -36.39,
    "max_lon": 144.86,
}

# API endpoints
ZONES_API_URL = "https://connect.pozi.com/userdata/bendigo-publisher/Pozi_Public_City_of_Greater_Bendigo/Waste_Collection_Zones.json"

# Test cases for validation
TEST_CASES = {
    "Bunnings Epsom": {
        "latitude": -36.701755710607394,
        "longitude": 144.31310883736967,
    },
    "Bunnings Bendigo": {
        "latitude": -36.808262837180514,
        "longitude": 144.24269331664098,
    },
    "Alfa Kitchen Bendigo": {
        "latitude": -36.758540554036315,
        "longitude": 144.2818129235716,
    },
    # "Boundary Test - Friday Calendar B": {
    #     # Point exactly halfway between [144.257674, -36.711266] and [144.250825, -36.715366]
    #     "latitude": -36.713316,  # (-36.711266 + -36.715366) / 2
    #     "longitude": 144.2542495   # (144.257674 + 144.250825) / 2
    # }
}

_LOGGER = logging.getLogger(__name__)

WASTE_NAMES = {"waste": "General Waste", "recycle": "Recycling", "green": "Green Waste"}

ICON_MAP = {"waste": "mdi:trash-can", "recycle": "mdi:recycle", "green": "mdi:leaf"}

COLLECTION_FREQUENCY = {"Weekly": 1, "Fortnightly": 2}


class Source:
    def __init__(self, latitude: float, longitude: float):
        """Initialize source with latitude and longitude coordinates.

        Args:
            latitude: Latitude coordinate (-37.07 to -36.39)
            longitude: Longitude coordinate (144.03 to 144.86)
        """
        try:
            # Convert inputs to float if they're strings
            self._latitude = float(latitude)
            self._longitude = float(longitude)

            if (
                not BENDIGO_BOUNDS["min_lat"]
                <= self._latitude
                <= BENDIGO_BOUNDS["max_lat"]
            ):
                raise SourceArgumentNotFound(
                    "latitude",
                    str(self._latitude),
                    f"Latitude must be between {BENDIGO_BOUNDS['min_lat']} and {BENDIGO_BOUNDS['max_lat']}",
                )
            if (
                not BENDIGO_BOUNDS["min_lon"]
                <= self._longitude
                <= BENDIGO_BOUNDS["max_lon"]
            ):
                raise SourceArgumentNotFound(
                    "longitude",
                    str(self._longitude),
                    f"Longitude must be between {BENDIGO_BOUNDS['min_lon']} and {BENDIGO_BOUNDS['max_lon']}",
                )
        except (ValueError, TypeError) as e:
            raise Exception(
                f"Invalid coordinate format. Please provide numeric values. Error: {str(e)}"
            )

    def fetch(self):
        try:
            zone_props = query_geojson_zones(
                ZONES_API_URL, self._latitude, self._longitude
            )
        except PoziGeoJsonError:
            raise Exception(
                f"Coordinates ({self._latitude}, {self._longitude}) not found in any Bendigo collection zone. "
                "Please check your location at https://www.bendigo.vic.gov.au/residents/general-waste-recycling-and-organics/bin-night",
            )

        _LOGGER.debug(
            "Found collection zone: %s",
            zone_props.get("Collection Reference"),
        )

        entries = []

        Source.__add_collection(
            zone_props.get("Collection Reference"),
            zone_props.get("Collection Day"),
            COLLECTION_FREQUENCY.get(zone_props.get("General Waste Frequency"), 0),
            zone_props.get("Next General Waste Pickup"),
            "waste",
            entries,
        )

        Source.__add_collection(
            zone_props.get("Collection Reference"),
            zone_props.get("Collection Day"),
            COLLECTION_FREQUENCY.get(zone_props.get("Recycling Frequency"), 0),
            zone_props.get("Next Recycling Pickup"),
            "recycle",
            entries,
        )

        Source.__add_collection(
            zone_props.get("Collection Reference"),
            zone_props.get("Collection Day"),
            COLLECTION_FREQUENCY.get(zone_props.get("Organics Frequency"), 0),
            zone_props.get("Next Organics Pickup"),
            "green",
            entries,
        )

        _LOGGER.debug("Entries: %s", entries)

        return entries

    @staticmethod
    def __add_collection(
        desc: str,
        day: str,
        weeks: int,
        start: str,
        collection_type: str,
        entries: List[Collection],
    ):
        if not desc:
            raise ValueError(
                f"Missing description for {WASTE_NAMES[collection_type]} collection"
            )

        if not start:
            raise ValueError(
                f"Missing start date for {WASTE_NAMES[collection_type]} collection"
            )

        if not day:
            raise ValueError(
                f"Missing collection day for {WASTE_NAMES[collection_type]} collection"
            )

        if not weeks or weeks < 1:
            raise ValueError(
                f"Invalid collection frequency for {WASTE_NAMES[collection_type]} collection"
            )

        try:
            start_date = datetime.strptime(start.strip(), "%d-%b-%Y").date()

            start_day = start_date.strftime("%A")

            # If the start date isn't on the specified day, find the next occurrence
            if start_day != day:
                days_ahead = [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                    "Sunday",
                ].index(day) - [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                    "Sunday",
                ].index(
                    start_day
                )
                if days_ahead <= 0:
                    days_ahead += 7
                start_date = start_date + timedelta(days=days_ahead)

            current_date = start_date
            end_date = datetime.now().date() + timedelta(days=365)

            while current_date <= end_date:
                entries.append(
                    Collection(
                        date=current_date,
                        t=WASTE_NAMES[collection_type],
                        icon=ICON_MAP[collection_type],
                    )
                )

                current_date = current_date + timedelta(weeks=weeks)

        except ValueError as e:
            raise ValueError(
                f"Invalid date format for {WASTE_NAMES[collection_type]} collection: {start}"
            ) from e
