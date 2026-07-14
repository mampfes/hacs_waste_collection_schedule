from __future__ import annotations

from datetime import datetime

from curl_cffi import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Straatbeeld Online"
DESCRIPTION = (
    "Source for Straatbeeld Online (afvalkalender.straatbeeld.online), "
    "a waste calendar platform used by several Dutch municipalities "
    "(e.g. Gemeente Drimmelen, Gemeente Geertruidenberg)."
)
URL = "https://afvalkalender.straatbeeld.online"
COUNTRY = "nl"

API_URL = "https://api.straatbeeld.online/v1/waste-calendar"

# Municipalities known to use this platform. Not exhaustive: any
# "<municipality>.afvalkalender.straatbeeld.online" instance will work,
# these are only used as suggestions if the provided value is not found.
KNOWN_MUNICIPALITIES = ["drimmelen", "geertruidenberg"]

TEST_CASES = {
    "Drimmelen, 4926CW 28": {
        "municipality": "drimmelen",
        "postal_code": "4926CW",
        "house_number": "28",
    },
    "Drimmelen, 4926 CW 28 (int house number)": {
        "municipality": "drimmelen",
        "postal_code": "4926 CW",
        "house_number": 28,
    },
}

ICON_MAP = {
    "gft": Icons.BIO_KITCHEN,
    "papier": Icons.PAPER,
    "pbd": Icons.PLASTIC_PACKAGING,
    "plastic": Icons.PLASTIC_PACKAGING,
    "rest": Icons.GENERAL_WASTE,
    "restafval": Icons.GENERAL_WASTE,
    "glas": Icons.GLASS,
    "textiel": Icons.TEXTILE,
    "grofvuil": Icons.BULKY,
    "kerstboom": Icons.CHRISTMAS_TREE,
    "kca": Icons.HAZARDOUS,
    "chemisch": Icons.HAZARDOUS,
}

PARAM_TRANSLATIONS = {
    "en": {
        "municipality": "Municipality",
        "postal_code": "Postal code",
        "house_number": "House number",
        "house_letter": "House letter/addition",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "municipality": (
            "Subdomain of the municipality's waste calendar, e.g. "
            "'drimmelen' for https://drimmelen.afvalkalender.straatbeeld.online"
        ),
        "postal_code": "Dutch postal code, e.g. 4926CW",
        "house_number": "House number, e.g. 28",
        "house_letter": (
            "House letter or addition, if applicable (optional, only "
            "needed when multiple addresses share the same postal code "
            "and house number)"
        ),
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Open your municipality's Straatbeeld Online waste calendar "
        "(e.g. https://drimmelen.afvalkalender.straatbeeld.online), the "
        "'municipality' argument is the first part of that URL "
        "(e.g. 'drimmelen'). Use the same postal code and house number "
        "you would enter on that page."
    ),
}


class Source:
    def __init__(
        self,
        municipality: str,
        postal_code: str,
        house_number: str | int,
        house_letter: str | None = None,
    ):
        self._municipality: str = municipality.strip().lower()
        self._postal_code: str = postal_code.replace(" ", "").upper()
        self._house_number: str | int = house_number
        self._house_letter: str | None = house_letter or None

    def fetch(self) -> list[Collection]:
        origin = f"https://{self._municipality}.afvalkalender.straatbeeld.online"

        session = requests.Session(impersonate="chrome")
        r = session.post(
            API_URL,
            json={
                "postal_code": self._postal_code,
                "house_number": str(self._house_number),
                "house_letter": self._house_letter,
            },
            headers={
                "Origin": origin,
                "Referer": f"{origin}/",
                "Accept": "application/json",
            },
            timeout=30,
        )

        if r.status_code == 404:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality", self._municipality, KNOWN_MUNICIPALITIES
            )
        if r.status_code == 422:
            raise SourceArgumentNotFound(
                "postal_code",
                f"{self._postal_code} {self._house_number}",
                "please check the postal code, house number and house letter.",
            )
        r.raise_for_status()

        data = r.json()

        entries = []
        for months in data.get("collections", {}).values():
            for items in months.values():
                for item in items:
                    collection_date = datetime.strptime(
                        item["date"]["formatted"], "%Y-%m-%d"
                    ).date()
                    for waste in item.get("data", []):
                        name = waste.get("name", "")
                        entries.append(
                            Collection(
                                date=collection_date,
                                t=waste.get("display_name", name),
                                icon=ICON_MAP.get(name.lower()),
                            )
                        )

        return entries
