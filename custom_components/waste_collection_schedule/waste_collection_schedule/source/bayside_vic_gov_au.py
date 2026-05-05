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

TITLE = "Bayside Council (Victoria)"
DESCRIPTION = "Source for Bayside Council rubbish collection."
URL = "https://bayside.vic.gov.au"
TEST_CASES = {
    "76 Royal Avenue Sandringham": {"street_address": "76 Royal Avenue Sandringham"},
}

ICON_MAP = {
    "Recycling": "mdi:recycle",
    "Food & Green Waste": "mdi:leaf",
    "Domestic Waste": "mdi:trash-can",
}

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://gis.bayside.vic.gov.au",
    instance="IntraMaps910",
    config_id="7a287c70-ea2d-4abd-943c-8bf55cf09fe5",
    project="1c8f869f-fa4a-4c39-b7bb-94641ee61597",
    module_id="5c590b56-e989-48a3-9bb8-207d4a388373",
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
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        try:
            with MapsClient(INTRAMAPS_CONFIG) as client:
                result = client.select_address(self._street_address)
        except IntraMapsSearchError as e:
            raise SourceArgumentNotFound("street_address", self._street_address) from e

        fields = extract_panel_fields(result["response"])

        entries = []
        for waste_type in ["Recycling", "Domestic Waste", "Food & Green Waste"]:
            value = fields.get(waste_type, "")
            if value:
                entries.extend(self._parse_collection_field(waste_type, value))

        return entries

    def _parse_collection_field(self, waste_type, value_text):
        """Parse collection field text.

        Handles formats like:
        - "Fortnightly on Thursday, Next: 16 Apr 2026"
        - "Weekly on Thursdays"
        """
        entries = []
        icon = ICON_MAP.get(waste_type, "mdi:trash-can-outline")

        date_match = re.search(r"Next:\s*(\d{1,2}\s+\w+\s+\d{4})", value_text)
        if date_match:
            try:
                next_date = datetime.strptime(date_match.group(1), "%d %b %Y").date()
                is_fortnightly = "fortnightly" in value_text.lower()
                interval = 14 if is_fortnightly else 7

                for i in range(13):
                    entries.append(
                        Collection(
                            date=next_date + timedelta(days=i * interval),
                            t=waste_type,
                            icon=icon,
                        )
                    )
            except ValueError:
                pass

        elif "weekly" in value_text.lower():
            day_match = re.search(r"on\s+(\w+day)", value_text, re.IGNORECASE)
            if day_match:
                day_name = day_match.group(1).lower().rstrip("s")
                weekday = WEEKDAYS.get(day_name)
                if weekday is not None:
                    today = datetime.now().date()
                    days_ahead = (weekday - today.weekday()) % 7
                    next_date = today + timedelta(days=days_ahead)

                    for i in range(26):
                        entries.append(
                            Collection(
                                date=next_date + timedelta(weeks=i),
                                t=waste_type,
                                icon=icon,
                            )
                        )

        return entries
