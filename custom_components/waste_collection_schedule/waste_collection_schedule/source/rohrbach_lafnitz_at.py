from typing import ClassVar

from waste_collection_schedule import Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource

TITLE = "Rohrbach an der Lafnitz"
DESCRIPTION = "Source for Rohrbach an der Lafnitz, Austria."
URL = "https://www.rohrbach-lafnitz.at"
COUNTRY = "at"

TEST_CASES: dict[str, dict] = {
    "All waste types": {},
}

ICON_MAP = {
    "Biomüll": Icons.BIO_KITCHEN,
    "Leichtverpackungen": Icons.RECYCLING,
    "Restmüll": Icons.GENERAL_WASTE,
    "Sperrmüll": Icons.BULKY,
}


class Source(RiSKommunalSource):
    BASE_URL = "https://www.rohrbach-lafnitz.at"
    ICON_MAP = ICON_MAP
    GNR = "2371"
    # Calendar IDs (do parameter) for each waste type
    ICS_CALENDARS: ClassVar = {
        "Biomüll": "MjI1MTc2NDk0",
        "Leichtverpackungen": "MjI1MTc2NDg4",
        "Restmüll": "MjI1MTc2NDky",
        "Sperrmüll & Heckenschnitt": "MjI1MTc2NDk2",
    }

    def fetch(self):
        return self.fetch_ics_by_label(self.GNR, self.ICS_CALENDARS)
