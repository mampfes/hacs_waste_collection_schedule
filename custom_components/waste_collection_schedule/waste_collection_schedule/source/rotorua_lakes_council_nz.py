import datetime
import logging
import re

import requests
from waste_collection_schedule import Collection, Icons

_LOGGER = logging.getLogger(__name__)

TITLE = "Rotorua Lakes Council"
DESCRIPTION = "Source for Rotorua Lakes Council"
URL = "https://www.rotorualakescouncil.nz"
API_URL = (
    "https://gis.rdc.govt.nz/server/rest/services/Core/RdcServices/MapServer/160/query"
)
ICON_MAP = {
    "Rubbish": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "FOGO": Icons.ORGANIC,
}
HEADERS = {"User-Agent": "waste-collection-schedule"}

# RubbishCollection3/4 hold the next two collections under the FOGO schedule
# introduced on 1 October 2026. RubbishCollection1/2 hold the legacy schedule.
SCHEDULE_FIELDS = ("RubbishCollection3", "RubbishCollection4")

# e.g. "Monday 05/10/2026 Recycling and FOGO"
#      "Wednesday 07/10/2026 Recycling and Rubbish (and FOGO for food premises)"
ENTRY_REGEX = re.compile(r"^\s*\w+\s+(\d{1,2}/\d{1,2}/\d{4})\s+(.+?)\s*$")

TEST_CASES = {
    "Test1": {"address": "1061 Haupapa Street"},
    "Test2": {"address": "369 state highway 33"},
    "Test3": {"address": "17 Tihi road"},
    "Test4": {"address": "12a robin st"},
    "Test5": {"address": "25 kaska rd"},
}


class Source:
    def __init__(self, address):
        self._address = address

    def fetch_coordinates(self):
        params = {
            "format": "json",
            "q": self._address,
        }
        try:
            response = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params=params,
                headers=HEADERS,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                raise ValueError(f"Geolocation failed for address: {self._address}")
            return float(data[0]["lat"]), float(data[0]["lon"])
        except Exception as e:
            raise ValueError(
                f"Geolocation failed for address: {self._address} with error: {e}"
            ) from e

    def fetch(self):
        lat, lon = self.fetch_coordinates()

        params = {
            "f": "json",
            "geometryType": "esriGeometryPoint",
            "geometry": f"{lon},{lat}",
            "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": ",".join(("OBJECTID", "Name", "Day", *SCHEDULE_FIELDS)),
            "returnGeometry": "false",
        }
        try:
            response = requests.get(API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise ValueError(f"API request failed: {e}") from e

        entries = []
        for feature in data.get("features", []):
            attributes = feature.get("attributes", {})
            for field in SCHEDULE_FIELDS:
                value = (attributes.get(field) or "").strip()
                match = ENTRY_REGEX.match(value)
                if not match:
                    if value:
                        _LOGGER.debug("Skipping non-date schedule value: %s", value)
                    continue

                date_str, types_str = match.groups()
                try:
                    date = datetime.datetime.strptime(date_str, "%d/%m/%Y").date()
                except ValueError:
                    _LOGGER.error("Date parsing error for value: %s", date_str)
                    continue

                # Drop notes such as "(and FOGO for food premises)" and "only"
                types_str = re.sub(r"\(.*?\)", "", types_str)
                types_str = types_str.strip().removesuffix("only").strip()

                for bin_type in types_str.split(" and "):
                    bin_type = bin_type.strip()
                    if not bin_type:
                        continue
                    if bin_type.upper() != "FOGO":
                        bin_type = bin_type.capitalize()
                    entries.append(
                        Collection(
                            date=date,
                            t=bin_type,
                            icon=ICON_MAP.get(bin_type),
                        )
                    )

        if not entries:
            raise ValueError(
                f"No collection entries found for address: {self._address}"
            )

        return entries
