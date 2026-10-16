from datetime import date, datetime, timedelta

import requests
from dateutil.rrule import WEEKLY, rrule

from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentException,
    SourceArgumentNotFound,
)

TITLE = "Digiroute"
DESCRIPTION = "Digiroute waste collection schedule"
URL = "https://digiroute.se"
COUNTRY = "se"

TEST_CASES = {
    "Värmdö": {
        "street_address": "Rosenmalmsvägen 8",
        "municipality": "varmdo",
    }
}

ICON_MAP = {
    "Tvåfack 1": Icons.RECYCLING,
    "Tvåfack 2": Icons.GENERAL_WASTE,
    "Matavfall": Icons.ORGANIC,
    "Hushåll": Icons.GENERAL_WASTE,
}


class Source:
    def __init__(
        self,
        street_address: str,
        municipality: str,
    ):
        if not street_address:
            raise SourceArgumentException(
                "street_address",
                "street_address is required",
            )

        if not municipality:
            raise SourceArgumentException(
                "municipality",
                "municipality is required",
            )

        self._street_address = street_address.strip()
        self._municipality = municipality.lower().strip()

        self._addresses_url = (
            f"https://digiroute.se/api/{self._municipality}/addresses"
        )

        self._session = requests.Session()

    def _get_address(self):
        response = self._session.get(
            self._addresses_url,
            params={
                "q": self._street_address,
                "limit": 20,
            },
            timeout=30,
        )

        response.raise_for_status()

        items = response.json()["data"]["items"]

        exact_matches = [
            item
            for item in items
            if item["streetAddress"].casefold()
            == self._street_address.casefold()
        ]

        if len(exact_matches) == 1:
            return exact_matches[0]

        if len(exact_matches) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "street_address",
                self._street_address,
                [item["label"] for item in exact_matches],
            )

        if items:
            raise SourceArgAmbiguousWithSuggestions(
                "street_address",
                self._street_address,
                [item["label"] for item in items],
            )

        raise SourceArgumentNotFound(
            "street_address",
            self._street_address,
        )

    @staticmethod
    def _find_first_date(weekday, parity):
        current = date.today()

        while True:
            current += timedelta(days=1)

            #
            # Digiroute:
            # 0=sunday
            # 1=monday
            # ...
            # 6=saturday
            #
            digiroute_weekday = (current.weekday() + 1) % 7

            if digiroute_weekday != weekday:
                continue

            week = current.isocalendar().week

            if parity == "odd" and week % 2 == 0:
                continue

            if parity == "even" and week % 2 == 1:
                continue

            return current

    def fetch(self):
        address = self._get_address()

        response = self._session.get(
            f"{self._addresses_url}/{address['id']}/delivery",
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()["data"]

        entries = []

        for container in data["containers"]:
            if container.get("job") != "deliver":
                continue

            start_date = self._find_first_date(
                container["collectionWeekday"],
                container["collectionWeekParity"],
            )

            for pickup_date in rrule(
                WEEKLY,
                dtstart=datetime.combine(
                    start_date,
                    datetime.min.time(),
                ),
                interval=2,
                count=26,
            ):
                fraction = container["fraction"]

                entries.append(
                    Collection(
                        date=pickup_date.date(),
                        t=fraction,
                        icon=ICON_MAP.get(fraction),
                    )
                )

        return sorted(entries, key=lambda x: x.date)
