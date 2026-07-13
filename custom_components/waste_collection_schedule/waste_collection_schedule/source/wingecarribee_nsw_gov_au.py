from datetime import datetime, timedelta, timezone

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import ArcGisError, geocode

TITLE = "Wingecarribee Shire Council"
DESCRIPTION = "Source for Wingecarribee Shire Council (NSW) waste collection."
URL = "https://www.wsc.nsw.gov.au"
COUNTRY = "au"
SOURCE_CODEOWNERS = ["@m1ckyb"]

TEST_CASES = {
    "Willow Road": {"address": "8 Willow Road, Bowral NSW 2576"},
    "Badgery Street": {"address": "12 Badgery Street, Willow Vale NSW 2575"},
    "Willow Drive": {"address": "56 Willow Drive, Moss Vale NSW 2577"},
}

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Garden Organics": Icons.GARDEN,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address within the Wingecarribee Shire (e.g. '8 Willow Road, Bowral NSW 2576')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

ZONE_SERVICE_URL = "https://utility.arcgis.com/usrsvcs/servers/f69ab833f6164175ae4e6e752d109cdb/rest/services/BinDay/BinDayZones1/FeatureServer"

HEADERS = {
    "Referer": "https://wscweb.maps.arcgis.com/",
    "Origin": "https://wscweb.maps.arcgis.com",
}


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        try:
            location = geocode(self._address)
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        x = location["x"]
        y = location["y"]

        geometry = {
            "x": x,
            "y": y,
            "spatialReference": {"wkid": 4326},
        }

        base_params = {
            "geometry": str(geometry).replace("'", '"'),
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "Bin,BinDate,BinZoneLabel",
            "returnGeometry": "false",
            "f": "json",
        }

        for layer_id in range(1, 11):
            url = f"{ZONE_SERVICE_URL}/{layer_id}/query"
            try:
                r = requests.get(url, params=base_params, headers=HEADERS, timeout=20)
                r.raise_for_status()
                data = r.json()
                features = data.get("features", [])
                if features:
                    attrs = features[0].get("attributes", {})
                    return self._build_schedule(attrs)
            except requests.RequestException:
                continue

        raise SourceArgumentNotFound("address", self._address)

    def _build_schedule(self, attrs: dict) -> list[Collection]:
        bin_type = attrs.get("Bin", "")
        bin_date_ms = attrs.get("BinDate")
        if not bin_date_ms or not bin_type:
            raise SourceArgumentNotFound("address", self._address)

        base_date = datetime.fromtimestamp(
            bin_date_ms / 1000, tz=timezone.utc
        ).date() + timedelta(days=1)

        today = datetime.now().date()

        weekday = base_date.weekday()

        next_red = today + timedelta(days=(weekday - today.weekday()) % 7)

        entries: list[Collection] = []

        for i in range(26):
            d = next_red + timedelta(weeks=i)
            entries.append(
                Collection(
                    date=d,
                    t="General Waste",
                    icon=ICON_MAP.get("General Waste"),
                )
            )

        next_main = base_date
        while next_main < today:
            next_main += timedelta(days=14)

        next_alt = next_main + timedelta(days=7)

        if bin_type == "RedYellow":
            recycling_start = next_main
            garden_start = next_alt
        else:
            garden_start = next_main
            recycling_start = next_alt

        for i in range(13):
            d = recycling_start + timedelta(weeks=i * 2)
            entries.append(
                Collection(
                    date=d,
                    t="Recycling",
                    icon=ICON_MAP.get("Recycling"),
                )
            )

        for i in range(13):
            d = garden_start + timedelta(weeks=i * 2)
            entries.append(
                Collection(
                    date=d,
                    t="Garden Organics",
                    icon=ICON_MAP.get("Garden Organics"),
                )
            )

        return entries
