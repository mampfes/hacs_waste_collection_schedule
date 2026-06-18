from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Marktgemeinde Edlitz"
DESCRIPTION = "Source for Marktgemeinde Edlitz, AT"
URL = "https://edlitz.at"
COUNTRY = "at"
TEST_CASES = {"TestSource": {}}
ICON_MAP = {
    "Biomüllabfuhr": Icons.BIO_KITCHEN,
    "Papier Tonne": Icons.PAPER,
    "Grüne Tonne": Icons.RECYCLING,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Restmüll": Icons.GENERAL_WASTE,
    "Restmüll mit Panoramastraße": Icons.GENERAL_WASTE,
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.edlitz.at"
    ICON_MAP = ICON_MAP
