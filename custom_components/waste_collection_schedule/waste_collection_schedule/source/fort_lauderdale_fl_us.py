from datetime import date, timedelta
from typing import Any

from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import (
    ArcGisError,
    geocode,
    query_feature_layer,
)

TITLE = "Fort Lauderdale, FL"
DESCRIPTION = (
    "Source for City of Fort Lauderdale, FL trash, recycling, bulk trash and "
    "yard waste collection."
)
URL = "https://www.fortlauderdale.gov/government/departments-i-z/public-works/operations/sanitation-operations/collection-programs"
COUNTRY = "us"

TEST_CASES = {
    "413 NW 15th Ave": {"address": "413 NW 15th Ave, Fort Lauderdale, FL 33311"},
    "100 N Andrews Ave": {"address": "100 N Andrews Ave, Fort Lauderdale, FL 33301"},
}

ICON_MAP = {
    "Trash": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Bulk Trash": Icons.BULKY,
    "Yard Waste": Icons.GARDEN,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Full street address including city and state (e.g. '413 NW 15th Ave, Fort Lauderdale, FL 33311')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your full street address including city and state. The address is "
    "geocoded and matched against the city's 'My Government Services' collection "
    "zones (https://gis.fortlauderdale.gov/MyGovernmentServices/).",
}

# City of Fort Lauderdale "My Government Services" MapServer (public, no login).
MAPSERVER = "https://gis.fortlauderdale.gov/arcgis/rest/services/MyGovernmentServices/MyGovernmentServices/MapServer"
LAYERS = {
    "Trash": 7,
    "Recycling": 8,
    "Bulk Trash": 9,
    "Yard Waste": 10,
}

WEEKDAY_FIELDS = [
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
    "SUNDAY",
]
# Flags telling in which occurrence (1st..4th) of the weekday in a month the
# pickup happens.
WEEK_FIELDS = ["WEEKONE", "WEEKTWO", "WEEKTHREE", "WEEKFOUR"]

OUT_FIELDS = ",".join(["SCHEDULE", *WEEKDAY_FIELDS, *WEEK_FIELDS])

DAYS_AHEAD = 182


def _yes(attrs: dict[str, Any], field: str) -> bool:
    return str(attrs.get(field) or "").strip().lower() == "yes"


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        try:
            location = geocode(self._address)
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        entries: list[Collection] = []
        found = False
        for waste_type, layer in LAYERS.items():
            try:
                features = query_feature_layer(
                    f"{MAPSERVER}/{layer}", geometry=location, out_fields=OUT_FIELDS
                )
            except ArcGisError:
                continue
            found = True
            for attrs in features:
                entries += self._dates(attrs, waste_type)

        if not found:
            # Address is outside of the City of Fort Lauderdale service area.
            raise SourceArgumentNotFound("address", self._address)

        return entries

    @staticmethod
    def _dates(attrs: dict[str, Any], waste_type: str) -> list[Collection]:
        weekdays = [i for i, f in enumerate(WEEKDAY_FIELDS) if _yes(attrs, f)]
        weeks = [i + 1 for i, f in enumerate(WEEK_FIELDS) if _yes(attrs, f)]
        weekly = str(attrs.get("SCHEDULE") or "").strip().lower() == "weekly"
        icon = ICON_MAP.get(waste_type)

        today = date.today()
        result: list[Collection] = []
        for offset in range(DAYS_AHEAD):
            d = today + timedelta(days=offset)
            if d.weekday() not in weekdays:
                continue
            # nth occurrence of this weekday within the month (1-based)
            occurrence = (d.day - 1) // 7 + 1
            if weekly or occurrence in weeks:
                result.append(Collection(date=d, t=waste_type, icon=icon))
        return result
