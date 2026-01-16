from datetime import date

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentException

TITLE = "Hudiksvall"
DESCRIPTION = "Source for Hudiksvall."
URL = "https://www.hudiksvall.se"
TEST_CASES = {
    "Kommunhuset": {"address": "Trädgårdsgatan 4 Hudiksvall"},
}

ICON_MAP = {
    "Restavfall": "mdi:trash-can",
    "Matavfall": "mdi:leaf",
    "Porslin": "mdi:coffee",
    "Returpapper": "mdi:package-variant",
    "Pappersförpackningar": "mdi:package-variant",
    "Plastförpackningar": "mdi:recycle",
    "Metallförpackningar": "mdi:recycle",
    "Färgade": "mdi:bottle-soda",
    "Ofärgade": "mdi:bottle-soda",
    "Ljuskällor": "mdi:lightbulb",
    "Småbatterier": "mdi:battery",
}

API_URL = "https://gis.hudiksvall.se/origoserver/EDPFuture"

HEADERS = {"User-Agent": "Mozilla/5.0"}


class Source:
    def __init__(self, address: str):
        self._address: str = address

    def fetch(self) -> list[Collection]:
        params = {"address": self._address}

        r = requests.get(API_URL, params=params, headers=HEADERS)
        r.raise_for_status()

        response = r.json()
        if not response:
            raise SourceArgumentException(
                "address",
                f"No returned building address for: {self._address}",
            )

        entries = []
        for container in response:
            date_ = self.parse_date(
                container["year"], container["week"], container["day"]
            )
            icon = ICON_MAP.get(container["type"])
            entries.append(Collection(date_, container["type"], icon))

        return entries

    @staticmethod
    def parse_date(year, week, weekday) -> date:
        swedish_weekdays = {
            "Måndag": 1,
            "Tisdag": 2,
            "Onsdag": 3,
            "Torsdag": 4,
            "Fredag": 5,
            "Lördag": 6,
            "Söndag": 7,
        }

        return date.fromisocalendar(year, week, swedish_weekdays[weekday])
