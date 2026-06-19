from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "St. Margarethen im Lungau"
DESCRIPTION = "Waste collection schedule for St. Margarethen im Lungau, Austria."
URL = "https://www.st.margarethen.salzburg.at"
COUNTRY = "at"
SOURCE_CODEOWNERS = ["@bbr111"]

TEST_CASES: dict[str, dict] = {
    "St. Margarethen im Lungau": {},
}

ICON_MAP = {
    "Abholung BIO-Tonne": Icons.ORGANIC,
    "Abholung Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Abholung Hausmüll": Icons.GENERAL_WASTE,
    "Abholung Altpapier": Icons.PAPER,
    "Abholung Altglas": Icons.GLASS,
    "Sperrmüllabfuhr": Icons.BULKY,
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.st.margarethen.salzburg.at"
    ICON_MAP = ICON_MAP
    RAISE_ON_EMPTY = True
    QUERY_PARAMS = {
        "bdatum": "31.12.9999",
        "blnr": "",
        "gnr_search": "0",
        "menuonr": "218716164",
    }
