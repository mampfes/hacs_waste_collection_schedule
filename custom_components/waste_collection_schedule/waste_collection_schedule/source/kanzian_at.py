from typing import ClassVar

from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "St. Kanzian am Klopeiner See"
DESCRIPTION = "Source for St. Kanzian am Klopeiner See, Austria."
URL = "https://www.kanzian.at"
COUNTRY = "at"

TEST_CASES = {
    "St. Kanzian": {},
}

ICON_MAP = {
    "Hausmüll": Icons.GENERAL_WASTE,
    "Restmüll": Icons.GENERAL_WASTE,
    "Biomüll": Icons.BIO_KITCHEN,
    "Bioabfall": Icons.BIO_KITCHEN,
    "Papier": Icons.PAPER,
    "Altpapier": Icons.PAPER,
    "Leicht- und Metallverpackungen": Icons.PLASTIC_PACKAGING,
    "Leichtverpackungen": Icons.PLASTIC_PACKAGING,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Gelbe Tonne": Icons.PLASTIC_PACKAGING,
    "Sperrmüll": Icons.BULKY,
    "Altglas": Icons.GLASS,
    "Problemstoff": Icons.HAZARDOUS,
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.kanzian.at"
    ICON_MAP = ICON_MAP
    RAISE_ON_EMPTY = True
    QUERY_PARAMS: ClassVar = {
        "bdatum": "31.12.9999",
        "detailonr": "225258384",
        "menuonr": "225275269",
        "typ": "225258384",
    }
