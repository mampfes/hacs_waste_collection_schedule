from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Baumkirchen"
DESCRIPTION = "Waste collection schedule for the municipality of Baumkirchen, Austria."
URL = "https://www.baumkirchen.gv.at"
COUNTRY = "at"
SOURCE_CODEOWNERS = ["@bbr111"]

TEST_CASES: dict[str, dict] = {"TestSource": {}}

ICON_MAP = {
    "Restmüll": Icons.GENERAL_WASTE,
    "Plastikmüll": Icons.PLASTIC_PACKAGING,
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.baumkirchen.gv.at"
    ICON_MAP = ICON_MAP
    RAISE_ON_EMPTY = True
    QUERY_PARAMS = {
        "bdatum": "31.12.9999",
        "menuonr": "218617457",
    }
