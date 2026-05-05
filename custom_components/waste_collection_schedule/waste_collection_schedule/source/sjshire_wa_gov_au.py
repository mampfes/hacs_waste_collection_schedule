from __future__ import annotations

from datetime import date, datetime, timedelta

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.IntraMaps import (
    IntegrationClient,
    IntegrationClientConfig,
    IntraMapsSearchError,
)

TITLE = "Shire of Serpentine Jarrahdale"
DESCRIPTION = "Source for www.sjshire.wa.gov.au Waste Collection Services"
URL = "https://www.sjshire.wa.gov.au"

TEST_CASES = {
    "Monday": {
        "address": "5 Pingaring Court BYFORD WA 6122",
        "predict": True,
    },
    "Tuesday": {"address": "865 South Western Highway BYFORD WA 6122"},
    "Wednesday": {"address": "701 Jarrahdale Road JARRAHDALE WA 6124"},
    "Thursday": {"address": "6 Paterson Street MUNDIJONG WA 6123"},
    "Friday": {"address": "1548 Kargotich Road MARDELLA WA 6125"},
}

ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
}

INTRAMAPS_CONFIG = IntegrationClientConfig(
    base_url="https://maps.sjshire.wa.gov.au",
    instance="IntraMaps22B",
    api_key="58383723-1396-43cc-a5cf-722e786208c6",
)

SEARCH_FORM = "de2aecaf-1e4d-4d25-8146-b0f0109aa458"
DETAILS_FORM = "a51626b7-3892-44f4-9fba-b0264486bda5"

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
    def __init__(self, address, predict=False):
        self._address = address
        self._predict = predict

    def fetch(self):
        client = IntegrationClient(INTRAMAPS_CONFIG)

        try:
            all_results = client.search_all(SEARCH_FORM, self._address)
        except IntraMapsSearchError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        # Find exact address match
        match = None
        addresses = []
        for result in all_results:
            addr = result.get("Address", "")
            addresses.append(addr)
            if self._address.lower().replace(" ", "").replace(
                ",", ""
            ) == addr.lower().replace(" ", "").replace(",", ""):
                match = result
                break

        if not match:
            raise SourceArgumentNotFoundWithSuggestions(
                "address", self._address, addresses
            )

        mapkey = match["mapkey"]
        dbkey = match["dbkey"]

        data = client.search(DETAILS_FORM, f"{mapkey},{dbkey}")

        # Rubbish — weekly on a named day
        day_rubbish = data.get("WasteCollectionDay", "").strip().lower()
        rubbish_weekday = WEEKDAYS.get(day_rubbish)
        if rubbish_weekday is not None:
            today = datetime.now().date()
            days_ahead = (rubbish_weekday - today.weekday()) % 7
            rubbish_date = today + timedelta(days=days_ahead)
        else:
            rubbish_date = None

        # Recycling — "[day] this/next week" (fortnightly)
        day_recycling = data.get("RecycleDay", "").strip().lower()
        recycle_date = self._parse_this_next_week(day_recycling)

        entries = []

        if rubbish_date:
            count = 4 if self._predict else 1
            for i in range(count):
                entries.append(
                    Collection(
                        date=rubbish_date + timedelta(weeks=i),
                        t="Rubbish",
                        icon=ICON_MAP["Rubbish"],
                    )
                )

        if recycle_date:
            count = 2 if self._predict else 1
            for i in range(count):
                entries.append(
                    Collection(
                        date=recycle_date + timedelta(weeks=i * 2),
                        t="Recycling",
                        icon=ICON_MAP["Recycling"],
                    )
                )

        return entries

    @staticmethod
    def _parse_this_next_week(text: str) -> date | None:
        """Parse '[day] this/next week' into a date."""
        parts = text.split()
        if not parts:
            return None

        day = parts[0]
        weekday = WEEKDAYS.get(day)
        if weekday is None:
            return None

        today = datetime.now().date()
        current_week_start = today - timedelta(days=today.weekday())
        target = current_week_start + timedelta(days=weekday)

        if "next" in text:
            target += timedelta(days=7)

        return target
