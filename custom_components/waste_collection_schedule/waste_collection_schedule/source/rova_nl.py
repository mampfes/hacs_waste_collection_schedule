from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Rova"
DESCRIPTION = "Source for Rova waste collection in the Netherlands."
URL = "https://www.rova.nl"
COUNTRY = "nl"

TEST_CASES = {
    "Lemele Lemelerweg 44": {
        "postalcode": "8148PC",
        "house_number": "44",
    },
    "Hardenberg Stationsstraat 1": {
        "postalcode": "7721AA",
        "house_number": "1",
        "addition": "",
    },
}

ICON_MAP = {
    "Gft": Icons.BIO_KITCHEN,
    "Pmd": Icons.RECYCLING,
    "Restafval": Icons.GENERAL_WASTE,
    "Papier": Icons.PAPER,
    "Glas": Icons.GLASS,
    "Textiel": Icons.TEXTILE,
    "Kerstboom": Icons.CHRISTMAS_TREE,
    "Snoeiafval": Icons.GARDEN,
}

PARAM_TRANSLATIONS = {
    "en": {
        "postalcode": "Postal code",
        "house_number": "House number",
        "addition": "Addition",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "postalcode": "Dutch postal code (4 digits + 2 letters, e.g. 8148PC)",
        "house_number": "House number",
        "addition": "House letter or addition (optional, only needed when multiple addresses share the same postal code and house number)",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Use the same postal code and house number you would enter at "
        "https://www.rova.nl/afvalkalender. If your address has a letter or "
        "addition, provide it in the 'addition' field."
    ),
}

API_URL = "https://www.rova.nl/api/waste-calendar/year"


class Source:
    def __init__(self, postalcode: str, house_number: str | int, addition: str = ""):
        self._postalcode = str(postalcode).replace(" ", "").upper()
        self._house_number = str(house_number).strip()
        self._addition = str(addition or "").strip()

    def fetch(self) -> list[Collection]:
        now = datetime.now()
        year = now.year
        entries = []
        exception = None

        try:
            entries = self._get_collections(year)
        except Exception as e:
            if now.month != 12:
                raise
            exception = e

        if now.month != 12:
            return entries

        # In December also fetch next year
        year += 1
        try:
            return entries + self._get_collections(year)
        except Exception:
            if exception:
                raise exception from None
            return entries

    def _get_collections(self, year: int) -> list[Collection]:
        params = {
            "postalcode": self._postalcode,
            "houseNumber": self._house_number,
            "addition": self._addition,
            "year": year,
        }

        r = requests.get(API_URL, params=params)
        r.raise_for_status()
        data = r.json()

        if not data:
            raise SourceArgumentNotFound(
                "postalcode",
                self._postalcode,
                "no waste calendar found for this address — please check postal code, house number and addition",
            )

        entries = []
        for item in data:
            date_str = item.get("date", "")
            waste_type = item.get("wasteType", {})
            title = waste_type.get("title", "")
            if not date_str or not title:
                continue

            # API returns ISO datetime strings like "2026-01-12T00:00:00Z"
            collection_date = datetime.fromisoformat(
                date_str.replace("Z", "+00:00")
            ).date()
            icon = ICON_MAP.get(title)
            entries.append(Collection(date=collection_date, t=title, icon=icon))

        return entries
