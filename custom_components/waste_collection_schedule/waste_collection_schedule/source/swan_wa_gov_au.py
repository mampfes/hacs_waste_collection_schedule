import re
from datetime import date

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

TITLE = "City of Swan"
DESCRIPTION = "Source for City of Swan waste collection."
URL = "https://www.swan.wa.gov.au"
COUNTRY = "au"

TEST_CASES = {
    "Stratton": {"address": "34 Oldenburg Pass Stratton"},
    "Midland": {"address": "307 Great Eastern Highway Midland"},
}

WEEKDAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

ICON_MAP = {
    "FOGO": Icons.BIO_KITCHEN,
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your street address including suburb "
    "(e.g. '34 Oldenburg Pass Stratton'). "
    "Search at https://www.swan.wa.gov.au/waste-and-sustainability/waste-and-recycling-services/bins/find-my-bin-day",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address with suburb (e.g. '34 Oldenburg Pass Stratton')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://swan.spatial.t1cloud.com",
    instance="spatial/intramaps",
    config_id="4c6eefa0-c035-40d1-b553-be6e06446b38",
    project="41a8ffbd-0da0-47c9-9957-b0dcb8a1bfc3",
    module_id="5a0205e5-ab05-4d94-a97f-2ae565ae48ff",
    selection_layer_filter="efd1a218-d9c4-43ec-b1bb-17514d03c3a3",
    default_selection_layer="efd1a218-d9c4-43ec-b1bb-17514d03c3a3",
)


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

        fields = extract_panel_fields(response)

        entries: list[Collection] = []

        self._add_fortnightly(
            entries, fields.get("Next General Waste Collection", ""), "General Waste"
        )
        self._add_fortnightly(
            entries, fields.get("Next Recycling Collection", ""), "Recycling"
        )
        # FOGO is collected weekly and reported as "Every Tuesday" instead of a date
        fogo = fields.get("Next FOGO Collection", "")
        if not self._add_weekly(entries, fogo, "FOGO"):
            self._add_fortnightly(entries, fogo, "FOGO")

        return entries

    @staticmethod
    def _add_weekly(entries: list[Collection], value: str, waste_type: str) -> bool:
        match = re.fullmatch(r"every\s+(\w+day)", value.strip(), re.IGNORECASE)
        if not match or match.group(1).lower() not in WEEKDAYS:
            return False

        weekday = WEEKDAYS.index(match.group(1).lower())
        for d in rrule(WEEKLY, byweekday=weekday, dtstart=date.today(), count=26):
            entries.append(
                Collection(date=d.date(), t=waste_type, icon=ICON_MAP.get(waste_type))
            )
        return True

    @staticmethod
    def _add_fortnightly(
        entries: list[Collection], date_str: str, waste_type: str
    ) -> None:
        if not date_str:
            return
        try:
            next_date = dateparse(date_str, dayfirst=True).date()
        except (ValueError, TypeError):
            return

        for d in rrule(WEEKLY, interval=2, dtstart=next_date, count=13):
            entries.append(
                Collection(date=d.date(), t=waste_type, icon=ICON_MAP.get(waste_type))
            )
