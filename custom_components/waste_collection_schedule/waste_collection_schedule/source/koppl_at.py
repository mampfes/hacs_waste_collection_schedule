from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Koppl"
DESCRIPTION = "Waste collection schedule for Koppl, Austria."
URL = "https://www.koppl.at"
COUNTRY = "at"

TEST_CASES = {
    "Koppl": {},
}

ICON_MAP = {
    "Restabfall 14-tägig": Icons.GENERAL_WASTE,
    "Restabfall monatlich": Icons.GENERAL_WASTE,
    "Restmüll": Icons.GENERAL_WASTE,
    "Bioabfall": Icons.ORGANIC,
    "Biomüll": Icons.ORGANIC,
    "Altpapier": Icons.PAPER,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Gelbe Tonne": Icons.PLASTIC_PACKAGING,
    "Sperrmüll": Icons.BULKY,
    "Altglas": Icons.GLASS,
    "Problemstoff": Icons.HAZARDOUS,
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.koppl.at"
    ICON_MAP = ICON_MAP
    RAISE_ON_EMPTY = True
    QUERY_PARAMS = {
        "bdatum": "31.12.9999",
        "detailonr": "225241960",
        "menuonr": "225241969",
        "typids": "225241960",
    }
