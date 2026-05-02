import re
from datetime import datetime, timedelta

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.IntraMaps import (
    IntraMapsSearchError,
    MapsClient,
    MapsClientConfig,
    extract_panel_fields,
)

TITLE = "City of Bayswater"
DESCRIPTION = "Source for City of Bayswater waste collection."
URL = "https://www.bayswater.wa.gov.au"
COUNTRY = "au"

TEST_CASES = {
    "Wholley St Bayswater": {"address": "9 Wholley St Bayswater"},
    "Ivory St Noranda": {"address": "14 Ivory St Noranda"},
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "FOGO": "mdi:leaf",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address with suburb (e.g. '9 Wholley St Bayswater')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://bayswater.spatial.t1cloud.com",
    instance="spatial/intramaps",
    config_id="359e0f03-92e0-4309-9024-f199f434a742",
    project="3c55e04f-d94e-4735-aecf-2e62b40bfd52",
    lite_config_id="221746d2-92cc-4591-a2da-bbecd930bb1b",
    module_id="d1e90488-605a-43ad-88cd-793e0a7d7c4e",
)

# Map IntraMaps field names to waste types
FIELD_MAP = {
    "FOGO Green Lid": "FOGO",
    "Waste Red Lid": "General Waste",
    "Recycling Yellow Lid": "Recycling",
}

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

        fields = extract_panel_fields(result["response"])

        entries: list[Collection] = []
        for field_name, waste_type in FIELD_MAP.items():
            value = fields.get(field_name, "")
            if value:
                entries.extend(self._parse_schedule(value, waste_type))

        return entries

    @staticmethod
    def _parse_schedule(text: str, waste_type: str) -> list[Collection]:
        """Parse schedule text like 'Every Friday' or 'Friday - 17 April 2026'."""
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

        # "[Day] - [Date]" — fortnightly with explicit next date
        match = re.match(r"\w+\s*-\s*(\d{1,2}\s+\w+\s+\d{4})", text)
        if match:
            try:
                next_date = datetime.strptime(match.group(1), "%d %B %Y").date()
                return [
                    Collection(
                        date=next_date + timedelta(weeks=i * 2),
                        t=waste_type,
                        icon=icon,
                    )
                    for i in range(13)
                ]
            except ValueError:
                pass

        return []
