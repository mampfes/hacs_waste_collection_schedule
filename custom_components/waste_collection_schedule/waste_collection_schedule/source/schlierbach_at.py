from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Marktgemeinde Schlierbach"
DESCRIPTION = "Source for Marktgemeinde Schlierbach waste collection."
URL = "https://www.schlierbach.at"
COUNTRY = "at"

TEST_CASES = {
    "Gemeinde Alle (no zone)": {},
    "Zone 1": {"zone": "1"},
    "Wohnhausanlagen": {"zone": "Wohnhausanlagen"},
}

ICON_MAP = {
    "Restabfall": Icons.GENERAL_WASTE,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Gelbe Tonne": Icons.PLASTIC_PACKAGING,
    "Altpapier": Icons.PAPER,
    "Altglas": Icons.GLASS,
    "Bioabfall": Icons.ORGANIC,
    "Problemstoff": Icons.HAZARDOUS,
    "Sperrmüll": Icons.BULKY,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "The zone argument is optional. Zone '1' adds the 4-weekly Restabfall schedule; "
    "zone 'Wohnhausanlagen' adds the Gelbe Tonne schedule for residential complexes. "
    "Leave it out to receive all events regardless of zone.",
    "de": "Das Argument 'zone' ist optional. Zone '1' ergänzt den 4-wöchentlichen "
    "Restabfall-Abholplan; Zone 'Wohnhausanlagen' ergänzt den Gelbe-Tonne-Plan für "
    "Wohnhausanlagen. Ohne Angabe werden alle Termine angezeigt.",
}

PARAM_TRANSLATIONS = {
    "en": {"zone": "Zone"},
    "de": {"zone": "Zone"},
}

PARAM_DESCRIPTIONS = {
    "en": {"zone": "Collection zone: '1' or 'Wohnhausanlagen' (optional)."},
    "de": {"zone": "Abholzone: '1' oder 'Wohnhausanlagen' (optional)."},
}

VALID_ZONES = ["1", "Wohnhausanlagen"]


class Source(RiSKommunalSource):
    BASE_URL = "https://www.schlierbach.at"
    ICON_MAP = ICON_MAP
    QUERY_PARAMS = {
        "sprache": "1",
        "menuonr": "225603725",
    }

    def __init__(self, zone: str | None = None):
        if zone is not None:
            zone = zone.strip()
            if zone not in VALID_ZONES:
                raise SourceArgumentNotFoundWithSuggestions(
                    "zone", zone, suggestions=VALID_ZONES
                )
        super().__init__(zone=zone)
