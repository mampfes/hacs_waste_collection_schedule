from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Piberbach"
DESCRIPTION = "Source for Piberbach, Austria."
URL = "https://www.piberbach.ooe.gv.at"
COUNTRY = "at"

TEST_CASES = {
    "Piberbacherstraße 20": {},
}

ICON_MAP = {
    "Bioabfall": Icons.ORGANIC,
    "Restabfall 2-wöchentlich": Icons.GENERAL_WASTE,
    "Restabfall 4-wöchentlich": Icons.GENERAL_WASTE,
    "Restabfall 6-wöchentlich": Icons.GENERAL_WASTE,
    "Altpapier": Icons.PAPER,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.piberbach.ooe.gv.at"
    ICON_MAP = ICON_MAP
    RAISE_ON_EMPTY = True
    QUERY_PARAMS = {
        "bdatum": "31.12.9999",
    }
