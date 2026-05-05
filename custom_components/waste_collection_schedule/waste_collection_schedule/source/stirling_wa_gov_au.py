import logging

import requests
from dateutil import parser
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import ArcGisGeocodeError, geocode

_LOGGER = logging.getLogger(__name__)

TITLE = "Stirling"
DESCRIPTION = "Source for Stirling."
URL = "https://www.stirling.wa.gov.au"
TEST_CASES = {
    "by_address": {"address": "100 Cedric Street, Stirling, WA, Australia"},
    "by_coords": {"lat": -31.9034183, "lon": 115.8320855},
    "by_coords_str": {"lat": "-31.8783052", "lon": "115.8157741"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your street address including suburb "
    "(e.g. '100 Cedric Street, Stirling, WA, Australia'), "
    "or provide latitude and longitude coordinates.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address with suburb (e.g. '100 Cedric Street, Stirling, WA, Australia')",
        "lat": "Latitude (optional if address is provided)",
        "lon": "Longitude (optional if address is provided)",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
        "lat": "Latitude",
        "lon": "Longitude",
    },
}

ICON_MAP = {
    "red": "mdi:trash-can",
    "green": "mdi:leaf",
    "greenverge": "mdi:pine-tree",
    "yellow": "mdi:recycle",
}

API_PATH = "/bincollectioncheck/getresult"
REFERER_PATH = "/waste-and-environment/waste-and-recycling/bin-collections"


class Source:
    def __init__(
        self,
        address: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
    ):
        self._address = address
        self._lat = float(lat) if lat is not None else None
        self._lon = float(lon) if lon is not None else None

        if not self._address and (self._lat is None or self._lon is None):
            raise ValueError(
                "Either 'address' or both 'lat' and 'lon' must be provided"
            )

    def _resolve_coordinates(self) -> tuple[float, float]:
        """Return (lat, lon), geocoding from address if needed."""
        if self._lat is not None and self._lon is not None:
            return self._lat, self._lon

        try:
            location = geocode(self._address)
        except ArcGisGeocodeError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        return location["y"], location["x"]

    def fetch(self) -> list[Collection]:
        lat, lon = self._resolve_coordinates()

        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "configid": "7c833520-7b62-4228-8522-fb1a220b32e8",
            "form": "57753bab-f589-44d7-8934-098b6d5c572f",
            "fields": f"{lon},{lat}",
            "apikeylookup": "Bin Day",
            "Origin": URL,
            "Referer": f"{URL}{REFERER_PATH}",
        }
        r = requests.get(f"{URL}{API_PATH}", headers=headers)
        r.raise_for_status()

        data = r.json()
        entries = []
        for collection in data:
            bin_type = None
            bin_date_str = None
            bin_date = None

            for arg in collection:
                if arg.get("name") == "type":
                    bin_type = arg.get("value")
                if arg.get("name") == "date":
                    bin_date_str = arg.get("value")
                    if not isinstance(bin_date_str, str):
                        continue
                    bin_date_str = bin_date_str.replace("  ", " ").strip()
                    try:
                        # Aug  7 2024
                        bin_date = parser.parse(bin_date_str).date()
                    except ValueError:
                        _LOGGER.warning("Could not parse date %s", bin_date_str)

            if bin_date is None:
                _LOGGER.warning("Could not find date for collection %s", bin_type)
                continue
            if bin_type is None:
                _LOGGER.warning("Skipping invalid collection record")
                continue
            icon = ICON_MAP.get(bin_type.lower())  # Collection icon
            entries.append(Collection(date=bin_date, t=bin_type, icon=icon))
        return entries
