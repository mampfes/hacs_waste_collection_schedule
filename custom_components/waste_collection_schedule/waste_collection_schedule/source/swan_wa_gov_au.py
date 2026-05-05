from dateutil.parser import parse as dateparse
from dateutil.rrule import WEEKLY, rrule
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
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

ICON_MAP = {
    "FOGO": "mdi:leaf",
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
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
        self._add_fortnightly(entries, fields.get("Next FOGO Collection", ""), "FOGO")

        return entries

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
