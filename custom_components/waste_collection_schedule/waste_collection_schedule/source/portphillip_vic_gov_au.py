from datetime import datetime, timedelta

from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.IntraMaps import (
    IntraMapsError,
    IntraMapsSearchError,
    MapsClient,
    MapsClientConfig,
    extract_panel_fields,
)

TITLE = "City of Port Phillip"
DESCRIPTION = "Source for City of Port Phillip waste collection."
URL = "https://www.portphillip.vic.gov.au"
COUNTRY = "au"

TEST_CASES = {
    "9 Spray Street Elwood": {"address": "9 Spray Street Elwood"},
    "99A Bridport Street Albert Park": {"address": "99A Bridport Street Albert Park"},
    "1 Beach Street Port Melbourne": {"address": "1 Beach Street Port Melbourne"},
}

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "FOGO": Icons.BIO_KITCHEN,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your street address including suburb "
    "(e.g. '9 Spray Street Elwood'). "
    "Search at https://www.portphillip.vic.gov.au/council-services/waste-recycling-and-rubbish/bins-and-collection-services",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address with suburb (e.g. '9 Spray Street Elwood')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://copp.spatial.t1cloud.com",
    instance="spatial/IntraMaps",
    config_id="15f21a6e-3939-4b70-b531-21309d0624de",
    project="3bf491de-10d3-42f0-be95-716bd4263526",
    lite_config_id="b0b09c2e-b120-4a07-84f3-fd8c1dbecb6e",
    module_id="e948c801-51b4-452a-87b5-2627e0e3e01a",
    selection_layer_filter="a6b80f49-ccbc-4b7c-8560-c1c15ac6164c",
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

        # "Bin Collection" is a weekday name, e.g. "Wednesday". The council
        # collects general waste, recycling and FOGO bins together, once a
        # week, on the same day.
        bin_day = fields.get("Bin Collection", "").strip()
        weekday = WEEKDAYS.get(bin_day.lower())
        if weekday is None:
            raise SourceArgumentNotFound("address", self._address)

        today = datetime.now().date()
        days_ahead = (weekday - today.weekday()) % 7
        next_date = today + timedelta(days=days_ahead)

        entries: list[Collection] = []
        for waste_type, icon in ICON_MAP.items():
            entries.extend(
                Collection(date=next_date + timedelta(weeks=i), t=waste_type, icon=icon)
                for i in range(26)
            )

        return entries
