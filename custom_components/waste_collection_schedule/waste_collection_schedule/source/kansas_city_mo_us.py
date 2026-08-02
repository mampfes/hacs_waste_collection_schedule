from datetime import date, timedelta

from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import (
    ArcGisError,
    geocode,
    query_feature_layer,
)

TITLE = "Kansas City, MO"
DESCRIPTION = "Source for Kansas City, Missouri trash and recycling collection."
URL = "https://www.kcmo.gov/city-hall/trash"
COUNTRY = "us"

TEST_CASES = {
    "Paseo": {"address": "4632 Paseo, Kansas City, MO 64110"},
    "Ward Parkway": {"address": "8330 Ward Parkway, Kansas City, MO"},
}

ICON_MAP = {
    "Trash": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Full street address including city and state (e.g. '4632 Paseo, Kansas City, MO 64110')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

# "Trash Route Boundary" layer (carries TRASHDAY). Native SR is WKID 102698;
# the server reprojects the WGS84 point returned by the geocoder automatically.
MAPSERVER_URL = "https://mapd.kcmo.org/kcgis/rest/services/DataLayers/MapServer/35"

WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        try:
            location = geocode(self._address)
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        try:
            features = query_feature_layer(
                MAPSERVER_URL,
                geometry=location,
                out_fields="TRASHDAY",
            )
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        attrs = features[0]
        pickup_day = (attrs.get("TRASHDAY") or "").strip().title()

        if not pickup_day or pickup_day not in WEEKDAYS:
            raise SourceArgumentNotFound("address", self._address)

        weekday = WEEKDAYS[pickup_day]
        today = date.today()
        days_ahead = (weekday - today.weekday()) % 7
        next_date = today + timedelta(days=days_ahead)

        entries: list[Collection] = []
        for i in range(26):
            d = next_date + timedelta(weeks=i)
            # KCMO collects trash and unlimited recycling on the same weekly day.
            entries.append(Collection(date=d, t="Trash", icon=ICON_MAP["Trash"]))
            entries.append(
                Collection(date=d, t="Recycling", icon=ICON_MAP["Recycling"])
            )
        return entries
