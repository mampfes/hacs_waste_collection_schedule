from typing import ClassVar

from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Stadtgemeinde Klosterneuburg"
DESCRIPTION = "Source for Stadtgemeinde Klosterneuburg waste collection."
URL = "https://www.klosterneuburg.at/Natur_Umwelt/Recycling/Muellabfuhr/Muellabfuhrkalender"
COUNTRY = "at"

TEST_CASES = {
    "Kierlinger Straße 10": {
        "street": "Kierlinger Straße",
        "house_number": "10",
    },
    "Adalbert Stifter-Gasse 1": {
        "street": "Adalbert Stifter-Gasse",
        "house_number": "1",
    },
}

ICON_MAP = {
    "Restmüll": Icons.GENERAL_WASTE,
    "Biomüll": Icons.BIO_KITCHEN,
    "Papiermüll": Icons.PAPER,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Sperrmüll": Icons.BULKY,
}

PARAM_TRANSLATIONS = {
    "de": {
        "street": "Straße",
        "house_number": "Hausnummer",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "Street name as shown on the Klosterneuburg website",
        "house_number": "House number",
    },
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.klosterneuburg.at"
    ICON_MAP = ICON_MAP
    SELECTION_URL = (
        "https://www.klosterneuburg.at/Natur_Umwelt/Recycling/Muellabfuhr/"
        "Muellabfuhrkalender"
    )
    QUERY_PARAMS: ClassVar = {
        "sprache": "1",
        "menuonr": "226582740",
    }

    def __init__(self, street, house_number):
        super().__init__(strasse=street, hausnummer=house_number)
