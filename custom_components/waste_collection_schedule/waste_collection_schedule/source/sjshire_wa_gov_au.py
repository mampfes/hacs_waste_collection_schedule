from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.IntraMaps import (
    IntraMapsSearchError,
    MapsClient,
    MapsClientConfig,
)

TITLE = "Shire of Serpentine Jarrahdale"
DESCRIPTION = "Source for www.sjshire.wa.gov.au Waste Collection Services"
URL = "https://www.sjshire.wa.gov.au"
COUNTRY = "au"

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
    "Rubbish": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
}

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://ser.spatial.t1cloud.com",
    instance="spatial/intramaps",
    config_id="93074f9e-ef2a-49d5-9866-91422949b9da",
    project="2e3adc22-b61d-4548-92d1-c1b02f9a30a3",
    module_id="bd33efd3-682b-478f-9dd1-82bdad11b52d",
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


RECYCLE_DAY_PATTERN = re.compile(r"^(\w+)\s*(this|next)\s+week$")


class Source:
    def __init__(self, address: str, predict: bool = False):
        self._address = address.strip()
        self._predict = predict

    def fetch(self) -> list[Collection]:
        search_address = re.sub(
            r"\s+WA\s+\d{4}\s*$",
            "",
            self._address,
            flags=re.IGNORECASE,
        )

        try:
            with MapsClient(INTRAMAPS_CONFIG) as client:
                result = client.select_address(search_address)
        except IntraMapsSearchError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        response = result["response"]
        if not isinstance(response, dict):
            raise SourceArgumentNotFound("address", self._address)

        fields = (
            response.get("infoPanels", {})
            .get("info1", {})
            .get("feature", {})
            .get("fields", [])
        )
        rubbish_date = None
        recycle_date = None
        for field in fields:
            value = field.get("value", {})
            if not isinstance(value, dict):
                continue
            column = value.get("column", "")
            text = value.get("value", "").strip().lower()
            if column == "WasteCollectionDay":
                rubbish_date = self._parse_weekday(text)
            elif column == "RecycleDay":
                recycle_date = self._parse_this_next_week(text)

        entries = []
        if rubbish_date:
            for i in range(4 if self._predict else 1):
                entries.append(
                    Collection(
                        date=rubbish_date + timedelta(weeks=i),
                        t="Rubbish",
                        icon=ICON_MAP["Rubbish"],
                    )
                )
        if recycle_date:
            for i in range(2 if self._predict else 1):
                entries.append(
                    Collection(
                        date=recycle_date + timedelta(weeks=i * 2),
                        t="Recycling",
                        icon=ICON_MAP["Recycling"],
                    )
                )
        return entries

    @staticmethod
    def _parse_weekday(text: str) -> date | None:
        weekday = WEEKDAYS.get(text)
        if weekday is None:
            return None
        today = datetime.now().date()
        return today + timedelta(days=(weekday - today.weekday()) % 7)

    @staticmethod
    def _parse_this_next_week(text: str) -> date | None:
        match = RECYCLE_DAY_PATTERN.fullmatch(text)
        if not match:
            return None
        weekday = WEEKDAYS.get(match.group(1))
        if weekday is None:
            return None
        today = datetime.now().date()
        target = today - timedelta(days=today.weekday()) + timedelta(days=weekday)
        if match.group(2) == "next":
            target += timedelta(days=7)
        return target
