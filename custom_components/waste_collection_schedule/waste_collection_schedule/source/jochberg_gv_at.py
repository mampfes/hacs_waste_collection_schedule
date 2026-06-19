from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Jochberg"
DESCRIPTION = "Waste collection schedule for the municipality of Jochberg, Austria."
URL = "https://www.jochberg.gv.at"
COUNTRY = "at"
SOURCE_CODEOWNERS = ["@bbr111"]

TEST_CASES: dict[str, dict] = {
    "Jochberg": {},
}

ICON_MAP = {
    "Biomüll": Icons.ORGANIC,
    "Restmüll": Icons.GENERAL_WASTE,
    "Altpapier": Icons.PAPER,
    "Papier": Icons.PAPER,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Gelbe Tonne": Icons.PLASTIC_PACKAGING,
    "Leichtverpackungen": Icons.PLASTIC_PACKAGING,
    "Sperrmüll": Icons.BULKY,
    "Altglas": Icons.GLASS,
    "Problemstoff": Icons.HAZARDOUS,
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.jochberg.gv.at"
    ICON_MAP = ICON_MAP
    GNR = "312"

    def fetch(self):
        return self.fetch_ics(self.GNR, ["MjI1NTczMjE0"])
