from datetime import date, datetime, timedelta, timezone

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import (
    ArcGisError,
    geocode,
    query_feature_layer,
)

TITLE = "Launceston City Council"
DESCRIPTION = "Source for Launceston City Council waste collection."
URL = "https://www.launceston.tas.gov.au"
COUNTRY = "au"

TEST_CASES = {
    "Southgate Dr": {"address": "40 Southgate Dr, Kings Meadows, TAS"},
    "Brisbane St": {"address": "68 Brisbane St, Launceston, TAS"},
}

ICON_MAP = {
    "Garbage": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "FOGO": "mdi:leaf",
    "Hard Waste": "mdi:sofa",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address (e.g. '40 Southgate Dr, Kings Meadows, TAS')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

WASTE_URL = "https://services.arcgis.com/yeXpdyjk3azbqItW/arcgis/rest/services/Waste/FeatureServer/0"

# Maps ArcGIS date fields to waste type names and whether they are fortnightly.
DATE_FIELDS = {
    "Garbagedate": ("Garbage", False),
    "Recycledate": ("Recycling", True),
    "Fogodate": ("FOGO", True),
    "Hardwastedate": ("Hard Waste", None),  # one-off
}


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        try:
            location = geocode(self._address)
            features = query_feature_layer(WASTE_URL, geometry=location)
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        attrs = features[0]
        service_types = (attrs.get("Servicetypes") or "").upper()

        entries: list[Collection] = []
        today = datetime.now().date()

        for field, (waste_type, fortnightly) in DATE_FIELDS.items():
            # Skip FOGO if not in service types
            if waste_type == "FOGO" and "F" not in service_types:
                continue

            ts = attrs.get(field)
            if not ts:
                continue

            base_date = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).date()
            icon = ICON_MAP.get(waste_type)

            if fortnightly is None:
                # Hard waste: include only if date is in the future
                if base_date >= today:
                    entries.append(Collection(date=base_date, t=waste_type, icon=icon))
            elif fortnightly:
                entries.extend(self._fortnightly_dates(base_date, waste_type, icon))
            else:
                entries.extend(self._weekly_dates(base_date, waste_type, icon))

        return entries

    @staticmethod
    def _weekly_dates(
        base_date: date, waste_type: str, icon: str | None
    ) -> list[Collection]:
        return [
            Collection(
                date=base_date + timedelta(weeks=i),
                t=waste_type,
                icon=icon,
            )
            for i in range(26)
        ]

    @staticmethod
    def _fortnightly_dates(
        base_date: date, waste_type: str, icon: str | None
    ) -> list[Collection]:
        return [
            Collection(
                date=base_date + timedelta(days=i * 14),
                t=waste_type,
                icon=icon,
            )
            for i in range(13)
        ]
