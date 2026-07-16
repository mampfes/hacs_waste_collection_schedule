from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Marktgemeinde Obdach"
DESCRIPTION = "Source for Marktgemeinde Obdach, AT"
URL = "https://www.obdach.gv.at/"
COUNTRY = "at"
TEST_CASES: dict[str, dict[str, str]] = {"TestSource": {}}
ICON_MAP = {
    "Biomüll": Icons.BIO_KITCHEN,
    "Altstoffsammelzentrum": Icons.NEWSPAPER,
    "Gelber Sack/Tonne": Icons.PLASTIC_PACKAGING,
    "Restmüll Abfuhrbereich 1": Icons.GENERAL_WASTE,
    "Restmüll Abfuhrbereich 2": Icons.GENERAL_WASTE,
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.obdach.gv.at"
    ICON_MAP = ICON_MAP
