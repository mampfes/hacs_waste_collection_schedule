from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Marktgemeinde Eggelsberg"
DESCRIPTION = "Source for Marktgemeinde Eggelsberg waste collection."
URL = "https://www.eggelsberg.at"
COUNTRY = "at"

TEST_CASES = {
    "Zone A": {"zone": "A"},
    "Zone B": {"zone": "B"},
}

ICON_MAP = {
    "Bioabfall": Icons.BIO_KITCHEN,
    "Altpapier": Icons.PAPER,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Restabfall 2-wöchentlich": Icons.GENERAL_WASTE,
    "Restabfall 4-wöchentlich": Icons.GENERAL_WASTE,
    "Restabfall 6-wöchentlich": Icons.GENERAL_WASTE,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Select your zone (A or B). This determines your Bioabfall (organic waste) "
    "collection schedule. All other waste types apply to all zones.",
    "de": "Wählen Sie Ihre Zone (A oder B). Dies bestimmt Ihren Bioabfall-"
    "Abholplan. Alle anderen Abfallarten gelten für alle Zonen.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "zone": "Collection zone (A or B)",
    },
    "de": {
        "zone": "Abholzone (A oder B)",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "zone": "Zone",
    },
    "de": {
        "zone": "Zone",
    },
}

VALID_ZONES = ["A", "B"]


class Source(RiSKommunalSource):
    BASE_URL = "https://www.eggelsberg.at"
    ICON_MAP = ICON_MAP
    VDATUM_TODAY = True
    QUERY_PARAMS = {
        "bdatum": "31.12.9999",
        "blnr": "",
        "gnr_search": "0",
        "menuonr": "224085238",
        "umkreis": "",
        "useronr": "0",
    }

    def __init__(self, zone: str):
        zone = zone.strip().upper()
        if zone not in VALID_ZONES:
            raise SourceArgumentNotFoundWithSuggestions(
                "zone", zone, suggestions=VALID_ZONES
            )
        super().__init__(zone=zone)
