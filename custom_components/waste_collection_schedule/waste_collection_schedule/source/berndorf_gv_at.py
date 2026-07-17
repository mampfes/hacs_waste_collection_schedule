from typing import ClassVar

from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Stadtgemeinde Berndorf"
DESCRIPTION = "Source for Stadtgemeinde Berndorf, Austria."
URL = "https://www.berndorf.gv.at"
COUNTRY = "at"
SOURCE_CODEOWNERS = ["@bbr111"]

TEST_CASES: dict[str, dict] = {
    "Berndorf": {},
}

ICON_MAP = {
    "Restmüll": Icons.GENERAL_WASTE,
    "Biotonne": Icons.ORGANIC,
    "Bioabfall": Icons.ORGANIC,
    "Biomüll": Icons.ORGANIC,
    "Altpapier": Icons.PAPER,
    "Papier": Icons.PAPER,
    "Gelbe Säcke": Icons.PLASTIC_PACKAGING,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Gelbe Tonne": Icons.PLASTIC_PACKAGING,
    "Aschetonne": Icons.COMBUSTIBLE,
    "Sperrmüll": Icons.BULKY,
    "Altglas": Icons.GLASS,
    "Problemstoff": Icons.HAZARDOUS,
    "Grünschnitt": Icons.GARDEN,
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.berndorf.gv.at"
    ICON_MAP = ICON_MAP
    RAISE_ON_EMPTY = True
    QUERY_PARAMS: ClassVar = {
        "sprache": "1",
        "menuonr": "226080602",
    }
