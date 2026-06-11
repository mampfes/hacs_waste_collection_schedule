import re
from datetime import date, datetime, timedelta

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

TITLE = "City of Mandurah"
DESCRIPTION = "Source for City of Mandurah waste collection."
URL = "https://www.mandurah.wa.gov.au/live/waste-and-recycling/bin-collections"
COUNTRY = "au"

TEST_CASES = {
    "Bouvard - Bouvard Estuary Foreshore": {
        "address": "Estuary RD BOUVARD",
    },
    "Clifton - Old Coast Road Buffer": {
        "address": "Old Coast RD CLIFTON",
    },
    "Coodanup - Coodanup Community College": {
        "address": "Steerforth DR COODANUP",
    },
    "Dawesville - Dawesville Foreshore": {
        "address": "Estuary RD DAWESVILLE",
    },
    "Dudley Park - Dudley Park Bowling Club": {
        "address": "Gillark ST DUDLEY PARK",
    },
    "Erskine - Erskine Ablution": {
        "address": "Bridgewater BVD ERSKINE",
    },
    "Falcon - Falcon Pavilion": {
        "address": "Flame ST FALCON",
    },
    "Greenfields - Bortolo Pavilion": {
        "address": "Bortolo DR GREENFIELDS",
    },
    "Halls Head - Halls Head Community Recreation Centre": {
        "address": "Fuchsia PL HALLS HEAD",
    },
    "Herron - Herron Foreshore": {
        "address": "Hexham CL HERRON",
    },
    "Lakelands - Lakelands Library and Community Centre": {
        "address": "49 Banksiadale GTE LAKELANDS",
    },
    "Madora Bay - Madora Bay Central Ablution": {
        "address": "Sabina DR MADORA BAY",
    },
    "Mandurah - Mandurah Administration Centre": {
        "address": "3 Peel ST MANDURAH",
    },
    "Meadow Springs - Quarry Adventure Park": {
        "address": "Pebble Beach BVD MEADOW SPRINGS",
    },
    "Parklands - Lakes Lawn Cemetery": {
        "address": "Stock RD PARKLANDS",
    },
    "San Remo - San Remo Beach": {
        "address": "Acheron RD SAN REMO",
    },
    "Silver Sands - Henson Reserve": {
        "address": "Henson ST SILVER SANDS",
    },
    "Wannanup - Port Bouvard Marina": {
        "address": "Rees PL WANNANUP",
    },
}

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your street address including suburb. "
    "Search at https://www.mandurah.wa.gov.au/live/waste-and-recycling/bin-collections",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address with suburb (e.g. '3 Peel ST MANDURAH')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://maps.mandurah.wa.gov.au",
    instance="IntraMaps910",
    config_id="00000000-0000-0000-0000-000000000000",
    project="a510900b-e9b6-48e2-a541-8f4ea5bc2214",
    lite_config_id="e7feb691-ab8c-40e9-a7ab-bd73b298b789",
    module_id="8e8074e1-317a-4de0-ac28-4d9739285994",
    default_selection_layer="6aac01c4-fdb9-4b3b-830e-31bc2814aaea",
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
            raise SourceArgumentNotFound("address", self._address)

        info_panels = response.get("infoPanels")
        info_panel = (
            info_panels.get("info1", {}) if isinstance(info_panels, dict) else {}
        )
        if not isinstance(info_panel.get("feature"), dict):
            raise SourceArgumentNotFound("address", self._address)

        fields = extract_panel_fields(response)

        general_waste_entries = self._get_weekly(
            fields.get("Refuse Day", ""), "General Waste"
        )
        recycling_entries = self._get_fortnightly(
            fields.get("Next Recycle Day is ", ""), "Recycling"
        )

        if not general_waste_entries or not recycling_entries:
            raise SourceArgumentNotFound("address", self._address)

        return general_waste_entries + recycling_entries

    @staticmethod
    def _get_weekly(weekday_str: str, waste_type: str) -> list[Collection]:
        weekday = WEEKDAYS.get(weekday_str.strip().casefold())
        if weekday is None:
            return []

        today = datetime.now().date()
        days_ahead = (weekday - today.weekday()) % 7
        next_date = today + timedelta(days=days_ahead)

        return [
            Collection(
                date=Source._adjust_for_holidays(d.date()),
                t=waste_type,
                icon=ICON_MAP.get(waste_type),
            )
            for d in rrule(WEEKLY, dtstart=next_date, count=26)
        ]

    @staticmethod
    def _get_fortnightly(date_str: str, waste_type: str) -> list[Collection]:
        if not date_str:
            return []

        match = re.search(r"(\d{1,2}\s+\w+\s+\d{4})", date_str)
        if not match:
            return []

        try:
            next_date = dateparse(match.group(1), dayfirst=True).date()
        except (TypeError, ValueError):
            return []

        return [
            Collection(
                date=Source._adjust_for_holidays(d.date()),
                t=waste_type,
                icon=ICON_MAP.get(waste_type),
            )
            for d in rrule(WEEKLY, interval=2, dtstart=next_date, count=13)
        ]

    @staticmethod
    def _adjust_for_holidays(collection_date: date) -> date:
        if collection_date.month == 12 and collection_date.day == 25:
            return collection_date + timedelta(days=1)
        return collection_date
