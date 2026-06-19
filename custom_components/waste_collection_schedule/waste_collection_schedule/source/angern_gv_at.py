from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Marktgemeinde Angern an der March"
DESCRIPTION = "Source for Marktgemeinde Angern an der March, Austria."
URL = "https://www.angern.at"
COUNTRY = "at"

TEST_CASES: dict[str, dict] = {"TestSource": {}}

ICON_MAP = {
    "Restmüll": Icons.GENERAL_WASTE,
    "Biotonne": Icons.ORGANIC,
    "Biomüll": Icons.ORGANIC,
    "Altpapier": Icons.PAPER,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Gelbe Tonne": Icons.PLASTIC_PACKAGING,
    "Grünschnitt": Icons.GARDEN,
    "Sperrmüll": Icons.BULKY,
    "Altglas": Icons.GLASS,
    "Recyclinghof": Icons.RECYCLING,
    "Problemstoff": Icons.HAZARDOUS,
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.angern.at"
    ICON_MAP = ICON_MAP
    RAISE_ON_EMPTY = True
