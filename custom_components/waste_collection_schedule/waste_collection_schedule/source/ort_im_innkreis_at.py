from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Ort im Innkreis"
DESCRIPTION = "Waste collection schedule for Ort im Innkreis, Austria."
URL = "https://www.ort-im-innkreis.at"
COUNTRY = "at"

TEST_CASES: dict[str, dict] = {
    "Default": {},
}

ICON_MAP = {
    "Bioabfall": Icons.ORGANIC,
    "Restabfall": Icons.GENERAL_WASTE,
    "Altpapier": Icons.PAPER,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Altglas": Icons.GLASS,
    "Sperrmüll": Icons.BULKY,
    "Problemstoff": Icons.HAZARDOUS,
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.ort-im-innkreis.at"
    ICON_MAP = ICON_MAP
    RAISE_ON_EMPTY = True
