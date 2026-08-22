from datetime import date, timedelta

from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import (
    ArcGisError,
    geocode,
    query_feature_layer,
)

TITLE = "Charleston, SC"
DESCRIPTION = "Source for City of Charleston, SC garbage and trash collection."
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

FEATURE_URL = "https://gis.charleston-sc.gov/arcgis2/rest/services/External/mapnetExternal/MapServer/10"

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
            features = query_feature_layer(
                FEATURE_URL,
                geometry=location,
                out_fields="DAY",
            )
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        pickup_day = (features[0].get("DAY") or "").strip().title()
        if pickup_day not in WEEKDAYS:
            raise SourceArgumentNotFound("address", self._address)

        today = date.today()
        days_ahead = (WEEKDAYS[pickup_day] - today.weekday()) % 7
        next_pickup = today + timedelta(days=days_ahead)

        return [
            Collection(
                date=next_pickup + timedelta(weeks=week),
                t="Garbage & Trash",
                icon=Icons.GENERAL_WASTE,
            )
            for week in range(WEEKS_AHEAD)
        ]
