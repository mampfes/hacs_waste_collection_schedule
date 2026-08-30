from datetime import date, timedelta

from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import (
    ArcGisError,
    geocode,
    query_feature_layer,
)

TITLE = "Charleston, SC"
DESCRIPTION = (
    "Source for City of Charleston, SC garbage and trash/yard-waste collection."
)
URL = "https://www.charleston-sc.gov/345/Environmental-Services"
COUNTRY = "us"

TEST_CASES = {
    "Downtown Charleston": {"address": "123 Coming St, Charleston, SC 29403"},
    "Johns Island (Trident Waste)": {
        "address": "2758 August Rd, Johns Island, SC 29455"
    },
    "Daniel Island (Berkeley County)": {
        "address": "1865 Pierce St, Charleston, SC 29492"
    },
}

SOURCE_CODEOWNERS = ["@dmkjr"]

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Full street address including city, state, and ZIP code.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

MAP_SERVER = "https://gis.charleston-sc.gov/arcgis2/rest/services/External/mapnetExternal/MapServer"

# Garbage and trash/yard-waste are collected on independent routes and can
# fall on different weekdays for the same address, so each layer is queried
# separately and surfaced as its own stream instead of being folded together.
LAYERS = [
    (f"{MAP_SERVER}/10", "Garbage", Icons.GENERAL_WASTE),
    (f"{MAP_SERVER}/11", "Trash & Yard Waste", Icons.GARDEN),
]

WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}

WEEKS_AHEAD = 26


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        try:
            location = geocode(self._address)
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        entries: list[Collection] = []
        for feature_url, waste_type, icon in LAYERS:
            try:
                features = query_feature_layer(
                    feature_url,
                    geometry=location,
                    out_fields="DAY",
                )
            except ArcGisError:
                # Not every address falls inside every route layer.
                continue

            pickup_day = (features[0].get("DAY") or "").strip().title()
            if pickup_day not in WEEKDAYS:
                continue

            today = date.today()
            days_ahead = (WEEKDAYS[pickup_day] - today.weekday()) % 7
            next_pickup = today + timedelta(days=days_ahead)

            entries.extend(
                Collection(
                    date=next_pickup + timedelta(weeks=week),
                    t=waste_type,
                    icon=icon,
                )
                for week in range(WEEKS_AHEAD)
            )

        if not entries:
            raise SourceArgumentNotFound("address", self._address)

        return entries
