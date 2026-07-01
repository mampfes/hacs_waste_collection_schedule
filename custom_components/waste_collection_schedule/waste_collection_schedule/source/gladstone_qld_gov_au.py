from __future__ import annotations

from datetime import date, timedelta

import requests

from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Gladstone Regional Council"
DESCRIPTION = "Waste collection schedule for Gladstone Regional Council, Queensland."
URL = "https://www.gladstone.qld.gov.au/Living-Here/Services/Waste-and-Recycling/Bin-Collection-Day"
COUNTRY = "au"
SOURCE_CODEOWNERS = ["@kodie-arch"]

TEST_CASES = {
    "85 J Hickey Avenue, Clinton": {
        "address": "85 J Hickey Avenue",
        "suburb": "CLINTON",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address, for example 85 J Hickey Avenue",
        "suburb": "Suburb/locality, for example CLINTON",
    }
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Use the street address and suburb shown in the Gladstone Regional Council bin collection lookup."
}

API_URL = "https://arcgisonpremise.gladstone.qld.gov.au/arcserver/rest/services/MapServices/WasteCollection/MapServer/0/query"

WEEK_2_ANCHOR = date(2026, 7, 3)

DAY_MAP = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
}


class Source:
    def __init__(self, address: str, suburb: str | None = None):
        self._address = address.strip()
        self._suburb = suburb.strip().upper() if suburb else None

    def _get_property(self) -> dict:
        where = f"UPPER(DBO.BaseParcel.MapAddress) LIKE '%{self._address.upper()}%'"

        if self._suburb:
            where += f" AND UPPER(DBO.BaseParcel.Suburb) = '{self._suburb}'"

        params = {
            "f": "json",
            "where": where,
            "outFields": (
                "DBO.BaseParcel.MapAddress,"
                "DBO.BaseParcel.Suburb,"
                "DBO.BaseParcel.WasteCollection,"
                "DBO.BaseParcel.RecycleCollectionDay,"
                "DBO.BaseParcel.GOBin"
            ),
            "returnGeometry": "false",
        }

        response = requests.get(API_URL, params=params, timeout=30)
        response.raise_for_status()

        features = response.json().get("features", [])

        if not features:
            raise SourceArgumentNotFound(
                "address",
                f"No matching address found for {self._address}.",
            )

        return features[0]["attributes"]

    @staticmethod
    def _next_weekday(target_weekday: int) -> date:
        today = date.today()
        return today + timedelta(days=(target_weekday - today.weekday()) % 7)

    @staticmethod
    def _is_week_2(collection_date: date) -> bool:
        weeks_since_anchor = (collection_date - WEEK_2_ANCHOR).days // 7
        return weeks_since_anchor % 2 == 0

    def fetch(self) -> list[Collection]:
        prop = self._get_property()

        collection_day = prop["DBO.BaseParcel.WasteCollection"].strip()
        recycle_week = prop["DBO.BaseParcel.RecycleCollectionDay"].strip()
        go_bin = (prop.get("DBO.BaseParcel.GOBin") or "").strip().upper()

        if collection_day not in DAY_MAP:
            raise ValueError(f"Unknown collection day returned by council: {collection_day}")

        if recycle_week not in {"Week 1", "Week 2"}:
            raise ValueError(f"Unknown recycling week returned by council: {recycle_week}")

        entries: list[Collection] = []
        first_collection = self._next_weekday(DAY_MAP[collection_day])

        for week_offset in range(12):
            collection_date = first_collection + timedelta(weeks=week_offset)

            entries.append(
                Collection(
                    date=collection_date,
                    t="General Waste",
                    icon=Icons.GENERAL_WASTE,
                )
            )

            is_week_2 = self._is_week_2(collection_date)

            is_recycling_week = (recycle_week == "Week 2" and is_week_2) or (
                recycle_week == "Week 1" and not is_week_2
            )

            if is_recycling_week:
                entries.append(
                    Collection(
                        date=collection_date,
                        t="Recycling",
                        icon=Icons.RECYCLING,
                    )
                )
            elif go_bin != "GO - NO":
                entries.append(
                    Collection(
                        date=collection_date,
                        t="Garden Organics",
                        icon=Icons.ORGANIC,
                    )
                )

        return entries
