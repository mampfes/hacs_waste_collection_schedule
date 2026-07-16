from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Marktgemeinde Gössendorf"
DESCRIPTION = "Source for Marktgemeinde Gössendorf, AT"
URL = "https://www.goessendorf.com/"
COUNTRY = "at"
TEST_CASES: dict[str, dict[str, str]] = {"TestSource": {}}
ICON_MAP = {
    "Bioabfall": Icons.BIO_KITCHEN,
    "Altpapier P1": Icons.PAPER,
    "Altpapier P2": Icons.PAPER,
    "Sperrmüll S1": Icons.BULKY,
    "Sperrmüll S2": Icons.BULKY,
    "Restmüll R1": Icons.GENERAL_WASTE,
    "Restmüll R2": Icons.GENERAL_WASTE,
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.goessendorf.com"
    ICON_MAP = ICON_MAP
