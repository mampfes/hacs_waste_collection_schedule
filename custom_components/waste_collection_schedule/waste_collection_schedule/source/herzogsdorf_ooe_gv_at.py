from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Herzogsdorf"
DESCRIPTION = "Source for Herzogsdorf, Austria."
URL = "https://www.herzogsdorf.ooe.gv.at"
COUNTRY = "at"

TEST_CASES = {
    "Herzogsdorf": {},
}

ICON_MAP = {
    "Restabfall wöchentlich": Icons.GENERAL_WASTE,
    "Restabfall 2-wöchentlich": Icons.GENERAL_WASTE,
    "Restabfall 4-wöchentlich": Icons.GENERAL_WASTE,
    "Restabfall 6-wöchentlich": Icons.GENERAL_WASTE,
    "Restabfall": Icons.GENERAL_WASTE,
    "Restmüll": Icons.GENERAL_WASTE,
    "Bioabfall": Icons.BIO_KITCHEN,
    "Biomüll": Icons.BIO_KITCHEN,
    "Altpapier": Icons.PAPER,
    "Papier": Icons.PAPER,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Gelbe Tonne": Icons.PLASTIC_PACKAGING,
    "Sperrmüll": Icons.BULKY,
    "Altglas": Icons.GLASS,
    "Problemstoff": Icons.HAZARDOUS,
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.herzogsdorf.ooe.gv.at"
    ICON_MAP = ICON_MAP
    RAISE_ON_EMPTY = True
    QUERY_PARAMS = {
        "menuonr": "225680057",
        "bdatum": "31.12.9999",
    }
