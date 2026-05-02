import re
from typing import Literal

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import ICS

TITLE = "Pointe-Claire (QC)"
DESCRIPTION = "Source for Pointe-Claire, Québec waste collection schedules."
URL = "https://www.pointe-claire.ca"
TEST_CASES = {
    "Sector A": {"sector": "A"},
    "Sector B": {"sector": "B"},
}

ICON_MAP = {
    "Organic Waste": "mdi:compost",
    "Recyclables": "mdi:recycle",
    "Household Waste": "mdi:trash-can",
    "Bulky Items": "mdi:sofa",
    "Christmas Tree Collection": "mdi:pine-tree",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Find your collection sector on the City of Pointe-Claire website at https://www.pointe-claire.ca/en/residents/public-works/waste-management/",
    "fr": "Trouvez votre secteur de collecte sur le site de la Ville de Pointe-Claire à https://www.pointe-claire.ca/residents/travaux-publics/gestion-des-dechets/",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "sector": "Collection sector (A or B)",
    },
    "fr": {
        "sector": "Secteur de collecte (A ou B)",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "sector": "Sector",
    },
    "fr": {
        "sector": "Secteur",
    },
}

SECTOR_URL_MAP: dict[str, str] = {
    "A": "https://raw.githubusercontent.com/jordanconway/pointe-claire-waste-calendars/refs/heads/main/pointe-claire-a.ics",
    "B": "https://raw.githubusercontent.com/jordanconway/pointe-claire-waste-calendars/refs/heads/main/pointe-claire-b.ics",
}

SECTOR_LITERAL = Literal["A", "B"]


class Source:
    def __init__(self, sector: SECTOR_LITERAL):
        self._sector = str(sector).upper().strip()
        self._ics = ICS()

    def fetch(self) -> list[Collection]:
        url = SECTOR_URL_MAP.get(self._sector)
        if url is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "sector", self._sector, list(SECTOR_URL_MAP.keys())
            )

        r = requests.get(url, timeout=30)
        r.raise_for_status()

        dates = self._ics.convert(r.text)
        entries = []
        for d in dates:
            # Strip " (Sector A)" / " (Sector B)" suffix — the sector is already
            # captured by the source configuration, so it's redundant in the type.
            collection_type = re.sub(r"\s*\(Sector [AB]\)$", "", d[1]).strip()
            entries.append(Collection(d[0], collection_type, ICON_MAP.get(collection_type)))
        return entries
