from typing import ClassVar

from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Fritzens"
DESCRIPTION = "Waste collection schedule for the municipality of Fritzens, Austria."
URL = "https://www.fritzens.gv.at"
COUNTRY = "at"

TEST_CASES: dict[str, dict] = {"TestSource": {}}

ICON_MAP = {
    "Biomüll": Icons.ORGANIC,
    "Restmüll": Icons.GENERAL_WASTE,
    "Kunststoffmüll": Icons.PLASTIC_PACKAGING,
    "Sperrmüll": Icons.BULKY,
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.fritzens.gv.at"
    ICON_MAP = ICON_MAP
    RAISE_ON_EMPTY = True
    QUERY_PARAMS: ClassVar = {
        "bdatum": "31.12.9999",
        "blnr": "",
        "gnr_search": "0",
        "menuonr": "219029364",
    }
