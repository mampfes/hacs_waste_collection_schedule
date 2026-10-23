import logging
from datetime import date, timedelta

import requests
from dateutil.easter import easter
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Wyndham City Council, Melbourne"
DESCRIPTION = "Source for Wyndham City Council rubbish collection."
URL = "https://wyndham.vic.gov.au"
TEST_CASES = {
    "Truganina South Primary School": {
        "street_address": "3-19 Parkvista Drive TRUGANINA 3029"
    },
    "Westbourne Grammar School": {"street_address": "300 Sayers Road TRUGANINA 3029"},
    "Werribee Mercy Hospital": {
        "street_address": "300-310 Princes Highway WERRIBEE 3030"
    },
    "Wyndham Park Primary School": {
        "street_address": "59-77 Kookaburra Avenue WERRIBEE 3030"
    },
}

# Public ArcGIS layer behind the council's bin day lookup.
API_URL = "https://services3.arcgis.com/lfHi3I35DWultHqw/arcgis/rest/services/BinCollectionData/FeatureServer/0/query"

ICON_MAP = {
    "Green Waste": Icons.GARDEN,
    "Garbage": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
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

# The layer only provides the collection day and the collection area ("Week" 1
# or 2). Recycling and green waste alternate weekly, with the two areas in
# opposite phase. Per the council's 2026/27 Waste and Recycling Calendar, the
# week starting Monday 19 October 2026 is a recycling week for area 1 and a
# green waste week for area 2.
RECYCLING_WEEK_AREA_1 = date(2026, 10, 19)

WEEKS = 26

_LOGGER = logging.getLogger(__name__)


def _is_holiday(d: date) -> bool:
    """Christmas Day, New Year's Day and Good Friday collections move one day later."""
    return (d.month, d.day) in ((12, 25), (1, 1)) or d == easter(d.year) - timedelta(
        days=2
    )


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def _query(self, where: str, count: int | None = None) -> list[dict]:
        params = {
            "where": where,
            "outFields": "EZI_ADD,Day,NewDay,Week",
            "returnGeometry": "false",
            "f": "json",
        }
        if count:
            params["resultRecordCount"] = count
        r = requests.get(API_URL, params=params)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise Exception(f"ArcGIS query failed: {data['error']}")
        return [f["attributes"] for f in data.get("features", [])]

    def _lookup(self) -> dict:
        address = " ".join(self._street_address.upper().split())
        if not address:
            raise SourceArgumentNotFound("street_address", self._street_address)
        quoted = address.replace("'", "''")

        rows = self._query(f"EZI_ADD = '{quoted}'")
        if rows:
            return rows[0]

        # no exact match: suggest addresses with the same number and street name
        prefix = " ".join(quoted.split()[:2])
        suggestions = [
            row["EZI_ADD"] for row in self._query(f"EZI_ADD LIKE '{prefix}%'", count=20)
        ]
        if suggestions:
            raise SourceArgumentNotFoundWithSuggestions(
                "street_address", self._street_address, suggestions
            )
        raise SourceArgumentNotFound("street_address", self._street_address)

    def fetch(self):
        row = self._lookup()
        _LOGGER.debug("Fetched property: %s", row)

        day = (row.get("NewDay") or row.get("Day") or "").strip().lower()
        if day not in WEEKDAYS:
            raise Exception(f"Unknown collection day '{day}' for {row['EZI_ADD']}")
        area = row.get("Week")
        if area not in (1, 2):
            raise Exception(f"Unknown collection week '{area}' for {row['EZI_ADD']}")

        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        entries = []
        for i in range(WEEKS):
            monday = week_start + timedelta(weeks=i)
            pickup = monday + timedelta(days=WEEKDAYS.index(day))
            if _is_holiday(pickup):
                pickup += timedelta(days=1)

            recycling_week = (monday - RECYCLING_WEEK_AREA_1).days // 7 % 2 == 0
            if area == 2:
                recycling_week = not recycling_week

            for waste_type in (
                "Garbage",
                "Recycling" if recycling_week else "Green Waste",
            ):
                entries.append(
                    Collection(date=pickup, t=waste_type, icon=ICON_MAP[waste_type])
                )
        return entries
