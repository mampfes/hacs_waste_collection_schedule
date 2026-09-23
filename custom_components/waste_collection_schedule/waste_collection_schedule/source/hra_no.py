import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "HRA (Hadeland og Ringerike Avfallsselskap)"
DESCRIPTION = (
    "Source for HRA waste collection in Hadeland (Gran, Jevnaker, Lunner), Norway."
)
URL = "https://hra.no"
COUNTRY = "no"

TEST_CASES = {
    "Myllavegen 1, 2742 GRUA": {"address": "Myllavegen 1, 2742 GRUA"},
    "Myllavegen 10": {"address": "Myllavegen 10"},
}

SEARCH_URL = "https://api.hra.no/search/address"
CALENDAR_URL = "https://hra.no/tommekalender/"
REQUEST_TIMEOUT = 30

MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "mai": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "okt": 10,
    "nov": 11,
    "des": 12,
}

ICON_MAP = {
    "Restavfall": Icons.GENERAL_WASTE,
    "Matavfall": Icons.BIO_KITCHEN,
    "Papir, papp og kartong": Icons.PAPER,
    "Plastemballasje": Icons.PLASTIC_PACKAGING,
    "Glass- og metallemballasje": Icons.GLASS,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Search for your address at hra.no/tommekalender and use the address "
        "as shown in the result list, e.g. 'Myllavegen 1, 2742 GRUA'."
    ),
    "de": (
        "Suche Deine Adresse auf hra.no/tommekalender und verwende sie so, wie sie "
        "in der Ergebnisliste angezeigt wird, z.B. 'Myllavegen 1, 2742 GRUA'."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Address as shown on hra.no/tommekalender, e.g. 'Myllavegen 1, 2742 GRUA'.",
    },
    "de": {
        "address": "Adresse wie auf hra.no/tommekalender angezeigt, z.B. 'Myllavegen 1, 2742 GRUA'.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {"address": "Address"},
    "de": {"address": "Adresse"},
}


def _normalize(value: str) -> str:
    return "".join(value.casefold().replace(",", "").split())


class Source:
    def __init__(self, address: str):
        self._address = address

    def _find_property(self) -> dict:
        r = requests.get(
            SEARCH_URL, params={"query": self._address}, timeout=REQUEST_TIMEOUT
        )
        r.raise_for_status()
        matches = r.json()

        norm = _normalize(self._address)
        exact = [m for m in matches if _normalize(m["name"]) == norm]
        if len(exact) == 1:
            return exact[0]
        if not exact:
            # Allow omitting postal code/place when the street address is unique.
            exact = [m for m in matches if _normalize(m["propertyName"]) == norm]
            if len(exact) == 1:
                return exact[0]
        candidates = exact or matches
        if not candidates:
            raise SourceArgumentNotFound("address", self._address)
        raise SourceArgumentNotFoundWithSuggestions(
            "address", self._address, sorted({m["name"] for m in candidates})
        )

    def fetch(self) -> list[Collection]:
        prop = self._find_property()

        r = requests.get(
            CALENDAR_URL,
            params={"query": prop["name"], "agreement": prop["agreementGuid"]},
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        today = datetime.date.today()
        year = today.year
        last_month = today.month
        entries: list[Collection] = []

        for row in soup.select("div.garbage-retrieval-row"):
            date_el = row.select_one("span.date")
            if date_el is None:
                continue
            day_str, _, month_str = date_el.get_text(strip=True).partition(".")
            month = MONTHS.get(month_str.strip()[:3].lower())
            if month is None:
                continue
            # The page shows dates in ascending order without a year.
            if month < last_month:
                year += 1
            last_month = month
            date = datetime.date(year, month, int(day_str))

            for col in row.select("div.types > div"):
                label = col.find_all("div", recursive=False)
                if not label:
                    continue
                waste_type = label[-1].get_text(strip=True)
                if not waste_type:
                    continue
                entries.append(
                    Collection(date=date, t=waste_type, icon=ICON_MAP.get(waste_type))
                )

        if not entries:
            raise SourceArgumentNotFound(
                "address", self._address, "no collection schedule found"
            )
        return entries
