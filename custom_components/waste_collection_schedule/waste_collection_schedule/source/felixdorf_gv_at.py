from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Gemeinde Felixdorf"
DESCRIPTION = "Source for Gemeinde Felixdorf, Austria."
URL = "https://www.felixdorf.gv.at"
COUNTRY = "at"

TEST_CASES: dict[str, dict] = {
    "Rayon 1": {"zone": "Rayon 1"},
    "Rayon 2": {"zone": "Rayon 2"},
    "All zones": {},
}

ICON_MAP = {
    "Biotonne": Icons.ORGANIC,
    "Restmüll": Icons.GENERAL_WASTE,
    "Papier": Icons.PAPER,
    "Windeltonne": Icons.GENERAL_WASTE,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Select your collection zone (Rayon 1 or Rayon 2). Leave blank to receive all zones.",
    "de": "Wählen Sie Ihre Abholzone (Rayon 1 oder Rayon 2). Leer lassen für alle Zonen.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "zone": "Collection zone (Rayon 1 or Rayon 2), or leave empty for all zones"
    },
    "de": {"zone": "Abholzone (Rayon 1 oder Rayon 2), oder leer für alle Zonen"},
}

PARAM_TRANSLATIONS = {
    "en": {"zone": "Zone"},
    "de": {"zone": "Zone"},
}

VALID_ZONES = ["Rayon 1", "Rayon 2"]


class Source(RiSKommunalSource):
    BASE_URL = "https://www.felixdorf.gv.at"
    ICON_MAP = ICON_MAP
    QUERY_PARAMS = {
        "bdatum": "31.12.9999",
        "blnr": "",
        "gnr_search": "0",
        "menuonr": "219384069",
    }

    def __init__(self, zone: str | None = None):
        if zone is not None:
            zone = zone.strip()
            if zone not in VALID_ZONES:
                raise SourceArgumentNotFoundWithSuggestions(
                    "zone", zone, suggestions=VALID_ZONES
                )
        super().__init__(zone=zone)
