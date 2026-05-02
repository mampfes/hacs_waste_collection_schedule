import datetime
import logging

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Mitchell Shire Council"
URL = "https://www.mitchellshire.vic.gov.au"
DESCRIPTION = "Source for Mitchell Shire Council, Victoria, Australia."

# Coordinates can be found by right-clicking your address in Google Maps and
# selecting "What's here?" — copy the lat/lon values shown.
TEST_CASES = {
    "Wallan": {
        "lat": -37.4195459,
        "lon": 144.9592853,
    },
    "Beveridge": {
        "lat": -37.48012709087705,
        "lon": 144.94518706976186,
    },
    "McDonalds Wallan": {"lat": -37.41290975665613, "lon": 144.97998167557827},
}

_LOGGER = logging.getLogger(__name__)

API_URL = "https://www.mitchellshire.vic.gov.au/simple-gov-app/api/resources/bin-collections/search"

# Map bin title to an MDI icon. The API also provides a `color` field
# (red/yellow/green/purple) which matches the physical bin lid colours.
ICON_MAP = {
    "General Rubbish": "mdi:trash-can",
    "Mixed Recycling": "mdi:recycle",
    "Food and Garden Organics": "mdi:leaf",
    "Glass Recycling": "mdi:bottle-wine",
}


class Source:
    def __init__(self, lat: float, lon: float):
        self._lat = lat
        self._lon = lon

    def fetch(self) -> list[Collection]:
        r = requests.get(
            API_URL,
            params={"lat": self._lat, "lng": self._lon},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()

        if data.get("result") != "success":
            raise ValueError(f"Unexpected API result: {data.get('result')}")

        entries = []
        for bin_type in data.get("data", []):
            title = bin_type.get("title", "Unknown")
            icon = ICON_MAP.get(title)

            for item in bin_type.get("collectionDates", []):
                try:
                    date = datetime.datetime.strptime(item["date"], "%Y-%m-%d").date()
                except (ValueError, KeyError) as e:
                    _LOGGER.warning("Could not parse date %s: %s", item, e)
                    continue

                entries.append(Collection(date=date, t=title, icon=icon))

        return entries
