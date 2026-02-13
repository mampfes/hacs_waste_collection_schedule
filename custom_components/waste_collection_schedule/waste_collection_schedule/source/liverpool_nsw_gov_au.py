from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Liverpool City Council (NSW)"
DESCRIPTION = "Source for Liverpool City Council (NSW, Australia)"
URL = "https://www.liverpool.nsw.gov.au/"
COUNTRY = "au"

TEST_CASES = {
    "Carnes Hill": {
        "address": "600 Kurrajong Road, Carnes Hill, NSW 2171",
    },
}

ICON_MAP = {
    "Garbage": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Organic": "mdi:leaf",
}

API_URL = "https://data.liverpool.nsw.gov.au/api/explore/v2.1/catalog/datasets/bin-collection-days/records"


class Source:
    def __init__(self, address: str):
        self._address = address

    def _search_address(self) -> str:
        params: dict[str, str | int] = {
            "where": f'gisaddress like "{self._address}"',
            "limit": 100,
        }
        r = requests.get(API_URL, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()

        if data["total_count"] == 0:
            raise SourceArgumentNotFound("address", self._address)

        addresses = [record["gisaddress"] for record in data["results"]]

        if data["total_count"] == 1:
            return addresses[0]

        raise SourceArgumentNotFoundWithSuggestions("address", self._address, addresses)

    def fetch(self) -> list[Collection]:
        matched_address = self._search_address()

        params: dict[str, str | int] = {
            "where": f'gisaddress = "{matched_address}"',
            "limit": 1,
        }
        r = requests.get(API_URL, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()

        if data["total_count"] == 0:
            raise SourceArgumentNotFound("address", self._address)

        fields = data["results"][0]
        entries = []
        end_date = date.today() + timedelta(days=365)

        bin_types = [
            ("garbagebin", "Garbage"),
            ("recyclebin", "Recycling"),
            ("organicbin", "Organic"),
        ]

        for field_prefix, bin_name in bin_types:
            week1_key = f"{field_prefix}_week1"
            schedule_key = f"{field_prefix}_schedule"

            if not fields.get(week1_key):
                continue

            start_date = date.fromisoformat(fields[week1_key])
            interval = fields.get(schedule_key, 7)

            current = start_date
            while current <= end_date:
                entries.append(
                    Collection(
                        date=current,
                        t=bin_name,
                        icon=ICON_MAP.get(bin_name, "mdi:trash-can"),
                    )
                )
                current += timedelta(days=interval)

        return entries
