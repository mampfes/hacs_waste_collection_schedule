import logging

import requests
from dateutil import parser
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "Stirling"
DESCRIPTION = "Source for Stirling."
URL = "https://www.stirling.wa.gov.au/"
TEST_CASES = {
    "-31.9034183 115.8320855": {"lat": -31.9034183, "lon": 115.8320855},
    "-31.878331, 115.815553": {"lat": "-31.8783052", "lon": "115.8157741"},
}


ICON_MAP = {
    "red": "mdi:trash-can",
    "green": "mdi:leaf",
    "greenverge": "mdi:pine-tree",
    "yellow": "mdi:recycle",
}


API_URL = "https://www.stirling.wa.gov.au/bincollectioncheck/getresult"


class Source:
    def __init__(self, lat: float, lon: float):
        if isinstance(lat, str):
            lat = float(lat)
        if isinstance(lon, str):
            lon = float(lon)

        self._lat: float = lat
        self._lon: float = lon

    def fetch(self) -> list[Collection]:
        headers = {
            "Host": "www.stirling.wa.gov.au",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "configid": "7c833520-7b62-4228-8522-fb1a220b32e8",
            "form": "57753bab-f589-44d7-8934-098b6d5c572f",
            "fields": f"{self._lon},{self._lat}",
            "apikeylookup": "Test Map Key",
            "X-Requested-With": "XMLHttpRequest",
            "Connection": "keep-alive",
        }
        r = requests.get(API_URL, headers=headers)
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
