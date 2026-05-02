import re
from datetime import datetime, timedelta

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.IntraMaps import (
    IntraMapsSearchError,
    MapsClient,
    MapsClientConfig,
)

TITLE = "City of Kwinana"
DESCRIPTION = "Source for City of Kwinana waste collection."
URL = "https://www.kwinana.wa.gov.au"
COUNTRY = "au"

TEST_CASES = {
    "Kwinana Town Centre": {"address": "1 Chisham Avenue KWINANA TOWN CENTRE"},
    "Wellard": {"address": "25 Breccia Parade WELLARD"},
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden Organics": "mdi:leaf",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your street address including suburb "
    "(e.g. '25 Breccia Parade WELLARD'). "
    "Search at https://www.kwinana.wa.gov.au/property-and-pets/waste-and-recycling/your-bins-and-collection-day",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address with suburb (e.g. '25 Breccia Parade WELLARD')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://kwinana.spatial.t1cloud.com",
    instance="spatial/intramaps",
    config_id="361cf79c-756a-4c28-903a-a8ed0347cacb",
    project="139a0e2d-fa83-4232-86e9-5e29f342e289",
    lite_config_id="96651193-ca0f-4797-95d7-98e972248fad",
    module_id="cbd33a46-14e5-4ca2-9009-03a51dcbc889",
    selection_layer_filter="c6352192-20e8-402c-85c1-ca8515d3cae3",
    default_selection_layer="c6352192-20e8-402c-85c1-ca8515d3cae3",
)

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

# Map IntraMaps column names to waste types
COLUMN_MAP = {
    "Rubbish_Collection_Day": "General Waste",
    "Recycle_Collection": "Recycling",
    "Garden Organics Collection": "Garden Organics",
}


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        try:
            with MapsClient(INTRAMAPS_CONFIG) as client:
                result = client.select_address(self._address)
        except IntraMapsSearchError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        response = result["response"]
        if not isinstance(response, dict):
            raise SourceArgumentNotFound("address", self._address)

        # Parse fields using column names (some fields have empty name/caption)
        raw_fields = (
            response.get("infoPanels", {})
            .get("info1", {})
            .get("feature", {})
            .get("fields", [])
        )

        entries: list[Collection] = []
        for field in raw_fields:
            value = field.get("value", {})
            if not isinstance(value, dict):
                continue
            column = value.get("column", "")
            text = value.get("value", "")
            waste_type = COLUMN_MAP.get(column)
            if waste_type and text:
                entries.extend(self._parse_schedule(text, waste_type))

        return entries

    @staticmethod
    def _parse_schedule(text: str, waste_type: str) -> list[Collection]:
        """Parse schedule text like 'Every Friday', 'Friday This Week', 'Friday Next Week'."""
        icon = ICON_MAP.get(waste_type)
        text_lower = text.strip().lower()

        # "Every [Day]" — weekly
        match = re.match(r"every\s+(\w+)", text_lower)
        if match:
            weekday = WEEKDAYS.get(match.group(1))
            if weekday is not None:
                today = datetime.now().date()
                days_ahead = (weekday - today.weekday()) % 7
                next_date = today + timedelta(days=days_ahead)
                return [
                    Collection(
                        date=next_date + timedelta(weeks=i),
                        t=waste_type,
                        icon=icon,
                    )
                    for i in range(26)
                ]

        # "[Day] This Week" or "[Day] Next Week" — fortnightly
        match = re.match(r"(\w+)\s+(this|next)\s+week", text_lower)
        if match:
            weekday = WEEKDAYS.get(match.group(1))
            if weekday is not None:
                today = datetime.now().date()
                current_week_start = today - timedelta(days=today.weekday())
                next_date = current_week_start + timedelta(days=weekday)
                if match.group(2) == "next":
                    next_date += timedelta(days=7)
                return [
                    Collection(
                        date=next_date + timedelta(weeks=i * 2),
                        t=waste_type,
                        icon=icon,
                    )
                    for i in range(13)
                ]

        return []
