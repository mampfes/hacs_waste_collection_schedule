import re
from datetime import datetime, timedelta

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.IntraMaps import (
    IntraMapsError,
    IntraMapsSearchError,
    MapsClient,
    MapsClientConfig,
    extract_panel_fields,
)

TITLE = "Fraser Coast Regional Council"
DESCRIPTION = "Source for Fraser Coast Regional Council waste collection."
URL = "https://www.frasercoast.qld.gov.au"
COUNTRY = "au"

TEST_CASES = {
    "Arbornine Road Glenwood": {"address": "57 Arbornine Road Glenwood"},
    "Tavistock Street Torquay": {"address": "77 Tavistock Street Torquay"},
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your street address including suburb "
    "(e.g. '57 Arbornine Road Glenwood'). "
    "Search at https://www.frasercoast.qld.gov.au/Services/Online-Services/Check-your-bin-day",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address with suburb (e.g. '57 Arbornine Road Glenwood')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://fcrc.spatial.t1cloud.com",
    instance="spatial/IntraMaps",
    config_id="e003842b-3af0-44a7-8bd8-45f9880f2c30",
    project="95d8904e-e9ef-4cac-88b5-def885f74f4d",
    lite_config_id="3727d4c0-1e2e-4eff-9669-b89f3a1919fe",
    module_id="b4b2af30-9b10-41a9-b9c9-3e253e2563a1",
    selection_layer_filter="93ccc583-6119-435f-845e-33deae245002",
    default_selection_layer="93ccc583-6119-435f-845e-33deae245002",
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
            raise IntraMapsError("Unexpected response format from IntraMaps")

        fields = extract_panel_fields(response)
        if not fields:
            raise SourceArgumentNotFound("address", self._address)

        entries: list[Collection] = []

        # "Bin Day" — weekly general waste, value is a weekday name e.g. "Friday"
        bin_day = fields.get("Bin Day", "").strip()
        if bin_day:
            entries.extend(
                self._weekly_dates(
                    bin_day.lower(), "General Waste", ICON_MAP["General Waste"]
                )
            )

        # "Recycling Day" — fortnightly, e.g. "Friday Week B; Next: 10 Apr 2026"
        recycling_day = fields.get("Recycling Day", "").strip()
        if recycling_day:
            entries.extend(self._parse_recycling(recycling_day))

        return entries

    @staticmethod
    def _weekly_dates(
        day_name: str, waste_type: str, icon: str, count: int = 26
    ) -> list[Collection]:
        weekday = WEEKDAYS.get(day_name)
        if weekday is None:
            return []

        today = datetime.now().date()
        days_ahead = (weekday - today.weekday()) % 7
        next_date = today + timedelta(days=days_ahead)

        return [
            Collection(date=next_date + timedelta(weeks=i), t=waste_type, icon=icon)
            for i in range(count)
        ]

    @staticmethod
    def _parse_recycling(text: str) -> list[Collection]:
        # Extract "Next: DD Mon YYYY" date
        match = re.search(r"Next:\s*(\d{1,2}\s+\w+\s+\d{4})", text)
        if not match:
            return []

        try:
            next_date = datetime.strptime(match.group(1), "%d %b %Y").date()
        except ValueError:
            return []

        icon = ICON_MAP["Recycling"]
        return [
            Collection(
                date=next_date + timedelta(weeks=i * 2),
                t="Recycling",
                icon=icon,
            )
            for i in range(13)
        ]
