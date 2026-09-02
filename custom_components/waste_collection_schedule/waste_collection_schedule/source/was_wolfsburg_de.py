from collections.abc import Iterable
from datetime import datetime
from typing import Any, NoReturn

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)

TITLE = "Wolfsburger Abfallwirtschaft und Straßenreinigung"
DESCRIPTION = "Source for waste collections for WAS-Wolfsburg, Germany."
URL = "https://was-wolfsburg.de"
TEST_CASES = {
    "Barnstorf": {"street": "Bahnhofspassage", "number": 1},
    "Sülfeld": {"street": "Bärheide", "number": 1},
}

API_URL = "https://abfuhrtermine.waswob.de/php/abfuhr_api.php"

ICON_MAP = {
    "Wertstofftonne": Icons.RECYCLING,
    "Bioabfall": Icons.BIO_KITCHEN,
    "Restabfall": Icons.GENERAL_WASTE,
    "Altpapier": Icons.PAPER,
}

PARAM_TRANSLATIONS = {
    "de": {
        "street": "Straße",
        "number": "Hausnummer",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "Street name as listed on https://abfuhrtermine.waswob.de/",
        "number": "House number as listed on https://abfuhrtermine.waswob.de/",
    },
    "de": {
        "street": "Straßenname wie auf https://abfuhrtermine.waswob.de/ angegeben",
        "number": "Hausnummer wie auf https://abfuhrtermine.waswob.de/ angegeben",
    },
}


class Source:
    def __init__(self, street: str | None, number: int | None):
        if street is None:
            raise SourceArgumentRequired("street", "Street must be set")
        if number is None:
            raise SourceArgumentRequired("number", "Number must be set")

        self._street: str = street
        self._number: str = str(number)

    def fetch(self) -> list[Collection]:
        r = requests.get(
            API_URL,
            params={
                "action": "termine",
                "strasse": self._street,
                "hausnummer": self._number,
            },
            timeout=30,
        )

        try:
            answer = r.json()
        except ValueError:
            r.raise_for_status()
            raise RuntimeError(f"Unexpected non-JSON response from {API_URL}") from None

        # The API answers unknown addresses with an HTTP error status and a JSON
        # error body, so the payload has to be inspected before the status code.
        if not isinstance(answer, list) or len(answer) == 0:
            self._raise_address_error(r)

        schedule = answer[0]

        entries: list[Collection] = []
        for name, icon in ICON_MAP.items():
            dates = schedule.get(name)
            if isinstance(dates, dict):
                raw_dates: Iterable[str] = dates.keys()
            elif isinstance(dates, list):
                raw_dates = dates
            else:
                continue
            for a in raw_dates:
                entries.append(
                    Collection(
                        date=datetime.strptime(a, "%Y-%m-%d").date(),
                        t=name,
                        icon=icon,
                    )
                )

        if not entries:
            self._raise_address_error(r)

        return entries

    def _raise_address_error(self, response: requests.Response) -> NoReturn:
        """Use the official street list to report which argument is wrong."""
        streets = self._fetch_streets()

        entry: dict[str, Any] | None = None
        for street in streets.values():
            if (
                str(street.get("strName", "")).strip().casefold()
                == self._street.strip().casefold()
            ):
                entry = street
                break

        if entry is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "street",
                self._street,
                sorted(str(s.get("strName", "")) for s in streets.values()),
            )

        numbers = [str(n) for n in entry.get("Hausnummer", [])]
        if self._number not in numbers:
            raise SourceArgumentNotFoundWithSuggestions("number", self._number, numbers)

        # Address is valid according to the street list, so this is a provider
        # side problem rather than a wrong argument.
        response.raise_for_status()
        raise RuntimeError(
            f"No collections returned for {self._street} {self._number}, "
            "the provider may be temporarily unavailable."
        )

    @staticmethod
    def _fetch_streets() -> dict[str, Any]:
        r = requests.get(API_URL, params={"action": "strassen"}, timeout=30)
        r.raise_for_status()
        streets = r.json()
        return streets if isinstance(streets, dict) else {}
