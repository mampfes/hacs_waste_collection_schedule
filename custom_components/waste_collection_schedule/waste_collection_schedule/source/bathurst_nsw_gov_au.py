import re
from datetime import datetime, timedelta

from dateutil.parser import parse as dateparse
from dateutil.rrule import WEEKLY, rrule
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.IntraMaps import (
    IntraMapsSearchError,
    MapsClient,
    MapsClientConfig,
    extract_panel_fields,
)

TITLE = "Bathurst Regional Council"
DESCRIPTION = "Source for Bathurst Regional Council (NSW) waste collection."
URL = (
    "https://www.bathurst.nsw.gov.au/Services/Waste-Recycling/Waste-Recycling-Calendar"
)
COUNTRY = "au"

SOURCE_CODEOWNERS = ["@Wolfieeewolf"]

TEST_CASES = {
    "Howick Street": {"address": "230 Howick St", "suburb": "Bathurst"},
    "Keppel Street": {"address": "1 Keppel St", "suburb": "Bathurst"},
}

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Organic": Icons.ORGANIC,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your street address and suburb "
    "(e.g. address '230 Howick St', suburb 'Bathurst'). "
    "Search at https://maps.bathurst.nsw.gov.au/IntraMaps23A/ApplicationEngine/frontend/mapbuilder/default.htm"
    "?configId=00000000-0000-0000-0000-000000000000"
    "&liteConfigId=24d1884e-fc58-45df-bca0-11bddc554781",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address (e.g. '230 Howick St')",
        "suburb": "Suburb (e.g. 'Bathurst')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
        "suburb": "Suburb",
    },
}

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://maps.bathurst.nsw.gov.au",
    instance="IntraMaps23A",
    project="00000000-0000-0000-0000-000000000000",
    lite_config_id="24d1884e-fc58-45df-bca0-11bddc554781",
    module_id="aa22688c-60ba-4db6-8db1-60f89ba2c5ed",
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
    def __init__(self, address: str, suburb: str):
        self._address = address.strip()
        self._suburb = suburb.strip()

    def fetch(self) -> list[Collection]:
        try:
            with MapsClient(INTRAMAPS_CONFIG) as client:
                result = client.select_address(self._address, self._suburb)
        except IntraMapsSearchError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        response = result["response"]
        if not isinstance(response, dict):
            raise SourceArgumentNotFound("address", self._address)

        fields = extract_panel_fields(response)
        if not fields:
            raise SourceArgumentNotFound("address", self._address)

        entries: list[Collection] = []

        entries.extend(
            self._weekly_dates(fields.get("Waste Collection Day", ""), "General Waste")
        )
        entries.extend(self._weekly_dates(fields.get("Organic", ""), "Organic"))
        entries.extend(
            self._fortnightly_dates(fields.get("Recycling", ""), "Recycling")
        )

        if not entries:
            raise SourceArgumentNotFound("address", self._address)

        return entries

    @staticmethod
    def _weekly_dates(
        day_name: str, waste_type: str, count: int = 26
    ) -> list[Collection]:
        weekday = WEEKDAYS.get(day_name.strip().casefold())
        if weekday is None:
            return []

        today = datetime.now().date()
        days_ahead = (weekday - today.weekday()) % 7
        next_date = today + timedelta(days=days_ahead)

        icon = ICON_MAP.get(waste_type)
        return [
            Collection(date=next_date + timedelta(weeks=i), t=waste_type, icon=icon)
            for i in range(count)
        ]

    @staticmethod
    def _fortnightly_dates(
        text: str, waste_type: str, count: int = 13
    ) -> list[Collection]:
        if not text:
            return []

        match = re.search(r"(\d{1,2}\s+\w+\s+\d{4})", text)
        if not match:
            return []

        try:
            next_date = dateparse(match.group(1), dayfirst=True).date()
        except (TypeError, ValueError):
            return []

        icon = ICON_MAP.get(waste_type)
        return [
            Collection(
                date=d.date(),
                t=waste_type,
                icon=icon,
            )
            for d in rrule(WEEKLY, interval=2, dtstart=next_date, count=count)
        ]
