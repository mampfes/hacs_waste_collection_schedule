import datetime

from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.service.Sepan import SepanClient

TITLE = "ALBA Swarzędz"
DESCRIPTION = "Source for ALBA waste collection in Swarzędz municipality, Poland."
URL = "https://www.alba.com.pl"
COUNTRY = "pl"

TEST_CASES = {
    "Bogucin, Boczna 7": {
        "city": "BOGUCIN",
        "street": "BOCZNA",
        "number": "7",
    },
    "Gortatowo, Królewska 12": {
        "city": "GORTATOWO",
        "street": "KRÓLEWSKA",
        "number": "12",
    },
    "Swarzędz, Józefa Rivoliego 2": {
        "city": "SWARZĘDZ",
        "street": "JÓZEFA RIVOLIEGO",
        "number": "2",
    },
}

SOURCE_CODEOWNERS = ["@kamilos-dev"]

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Open https://www.alba.com.pl/odbior_odpadow_wywoz_smieci/swarzedz "
        "and use the schedule search form. Select your city, street and house "
        "number from the dropdowns and use those exact values (uppercase) as "
        "the source arguments."
    ),
}

PARAM_TRANSLATIONS = {
    "en": {
        "city": "City",
        "street": "Street",
        "number": "House number",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "city": "City name in uppercase, e.g. SWARZĘDZ",
        "street": "Street name in uppercase, e.g. JÓZEFA RIVOLIEGO",
        "number": "House/building number, e.g. 2",
    },
}

ICON_MAP = {
    "Zmieszane odpady komunalne": Icons.GENERAL_WASTE,
    "Metale i tworzywa sztuczne": Icons.RECYCLING,
    "Papier": Icons.PAPER,
    "Szkło": Icons.GLASS,
    "Bioodpady": Icons.ORGANIC,
    "Bioodpady - Drzewka świąteczne": Icons.CHRISTMAS_TREE,
    "Odpady wystawkowe": Icons.BULKY,
}

# The ALBA deployment's harmonogram path is year-suffixed; try the current
# year first and fall back to the last known-good folder if the council
# hasn't rolled over yet (see issue #6749).
_KNOWN_YEAR_SUFFIX = "2025_swarzedz"


def _base_urls() -> list[str]:
    year = datetime.datetime.now().year
    return [
        f"https://sepan-wroclaw.alba.com.pl/harmonogram{year}_swarzedz",
        f"https://sepan-wroclaw.alba.com.pl/harmonogram{_KNOWN_YEAR_SUFFIX}",
    ]


class Source:
    def __init__(self, city: str = "", street: str = "", number: str = ""):
        self._client = SepanClient(_base_urls())
        self._address_id = self._client.resolve_address(city, street, number)

    def fetch(self) -> list[Collection]:
        entries = self._client.fetch_schedule(self._address_id)
        return [
            Collection(date=date, t=waste_type, icon=ICON_MAP.get(waste_type))
            for date, waste_type in entries
        ]
