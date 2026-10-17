from datetime import date, timedelta

import requests

from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Digiroute"
DESCRIPTION = "Source for Digiroute waste collection schedules."
URL = "https://digiroute.se"
COUNTRY = "se"

EXTRA_INFO = [
    {
        "title": "Värmdö kommun",
        "url": "https://www.varmdo.se",
        "default_params": {
            "service_provider": "Värmdö",
        },
    }
]

TEST_CASES = {
    "Rosenmalmsvägen 8": {
        "service_provider": "Värmdö",
        "street_address": "Rosenmalmsvägen 8",
    },
    "Rosenmalmsvägen 22": {
        "service_provider": "Värmdö",
        "street_address": "Rosenmalmsvägen 22",
    },
    "Stenolles Backe 6": {
        "service_provider": "Värmdö",
        "street_address": "Stenolles Backe 6",
    },
    "Mastvägen 10": {
        "service_provider": "Värmdö",
        "street_address": "Mastvägen 10",
    },
}

ICON_MAP = {
    "Tvåfack 1": Icons.RECYCLING,
    "Tvåfack 2": Icons.GENERAL_WASTE,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter municipality name and street address exactly "
        "as used by the Digiroute service."
    )
}

PARAM_TRANSLATIONS = {
    "en": {
        "service_provider": "Municipality",
        "street_address": "Street Address",
    }
}


class Source:
    def __init__(
        self,
        street_address: str,
        service_provider: str,
    ):
        self._street_address = street_address.strip()

        self._service_provider = (
            service_provider.lower()
            .replace("å", "a")
            .replace("ä", "a")
            .replace("ö", "o")
        )

        self._api_url = (
            f"https://digiroute.se/api/{self._service_provider}"
        )

    def _get_address(self):
        response = requests.get(
            f"{self._api_url}/addresses",
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

        if items:
            raise SourceArgumentNotFoundWithSuggestions(
                "street_address",
                self._street_address,
                [item["label"] for item in items],
            )

        raise SourceArgumentNotFound(
            "street_address",
            self._street_address,
        )

    @staticmethod
    def _matches_schedule(
        current_date: date,
        weekday: int,
        parity: str,
    ) -> bool:
        if current_date.isoweekday() != weekday:
            return False

        week = current_date.isocalendar().week

        if parity == "odd":
            return week % 2 == 1

        if parity == "even":
            return week % 2 == 0

        return False

    def fetch(self):
        address = self._get_address()

        response = requests.get(
            f"{self._api_url}/addresses/{address['id']}/delivery",
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()["data"]

        entries = []

        today = date.today()
        end_date = today + timedelta(weeks=8)

        for container in data["containers"]:
            if container.get("job") != "deliver":
                continue

            fraction = container["fraction"]
            weekday = container["collectionWeekday"]
            parity = container["collectionWeekParity"]

            current = today

            while current <= end_date:
                if self._matches_schedule(
                    current,
                    weekday,
                    parity,
                ):
                    entries.append(
                        Collection(
                            current,
                            fraction,
                            icon=ICON_MAP.get(fraction),
                        )
                    )

                current += timedelta(days=1)

        return sorted(entries, key=lambda x: x.date)
