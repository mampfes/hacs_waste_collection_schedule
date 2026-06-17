from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Dienten am Hochkönig"
DESCRIPTION = "Waste collection schedule for Dienten am Hochkönig, Austria."
URL = "https://www.dienten.gv.at"
COUNTRY = "at"

TEST_CASES = {
    # no input required as the waste collection site (dienten.gv.at) does not
    # have any address specific requirement
    "Dorf 53": {},
}

ICON_MAP = {
    "Restmüll": Icons.GENERAL_WASTE,
    "Biotonne": Icons.ORGANIC,
    "Gelbe Tonne": Icons.RECYCLING,
    "Gelber Sack": Icons.RECYCLING,
    "Papier Gewerbe": Icons.PAPER,
    "Karton Gewerbe": Icons.PAPER,
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.dienten.gv.at"
    ICON_MAP = ICON_MAP
    RAISE_ON_EMPTY = True
    QUERY_PARAMS = {
        "bdatum": "31.12.9999",
        "blnr": "",
        "gnr_search": "0",
        "menuonr": "218643352",
    }
