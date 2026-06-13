import logging
from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Repentigny (QC)"
DESCRIPTION = "Source script for Ville de Repentigny waste collection using the city's calendar JSON"
URL = "https://collectes-repentigny.coudmain.ca/"

TEST_CASES = {
    "Sector A": {"sector": "A"},
    "Sector B": {"sector": "B"},
    "Sector C": {"sector": "C"},
    "Sector D": {"sector": "D"},
    "Sector E": {"sector": "E"},
    "Sector F": {"sector": "F"},
}

ICON_MAP = {
    "R": Icons.RECYCLING,
    "R+": Icons.RECYCLING,
    "O": Icons.ORGANIC,
    "O+": Icons.ORGANIC,
    "D": Icons.GENERAL_WASTE,
    "S": Icons.CHRISTMAS_TREE,
    "B": Icons.GARDEN,
    "E": Icons.BULKY,
}

LABEL_MAP = {
    "R": "Recyclables",
    "R+": "Recyclables + surplus accepté",
    "O": "Matières organiques",
    "O+": "Organiques + résidus verts",
    "D": "Déchets",
    "S": "Sapins",
    "B": "Branches",
    "E": "Encombrants",
}

LOGGER = logging.getLogger(__name__)

PARAM_TRANSLATIONS = {
    "en": {
        "sector": "Sector",
    },
    "fr": {
        "sector": "Secteur",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "sector": "Your waste collection sector (A, B, C, D, E, or F)",
    },
    "fr": {
        "sector": "Votre secteur de collecte des déchets (A, B, C, D, E ou F)",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": 'Enter your sector manually if you know it from the <a href="https://repentigny.ca/services/citoyens/collectes">collection calendar</a>.',
    "fr": 'Entrez votre secteur manuellement si vous le connaissez d\'après le <a href="https://repentigny.ca/services/citoyens/collectes">calendrier de collecte</a>.',
}

COUNTRY = "ca"


class Source:
    def __init__(self, sector: str | None = None):
        self._sector = sector

        if not sector:
            raise SourceArgumentNotFound(
                "sector", "", "please provide a sector (A, B, C, D, E, or F)"
            )

        if sector not in ["A", "B", "C", "D", "E", "F"]:
            raise SourceArgumentNotFound(
                "sector", sector, "please provide a valid sector (A, B, C, D, E, or F)"
            )

    def fetch(self):
        now = datetime.now()
        base_url = "https://collectes-repentigny.coudmain.ca/data"

        # Try current year first, fall back to next year
        for year in (now.year, now.year + 1):
            url = f"{base_url}/calendrier-{year}.json"
            response = requests.get(url, timeout=30)
            if response.ok:
                data = response.json()
                break
        else:
            response.raise_for_status()
            data = response.json()
        entries = []
        today = now.date()

        for entry in data["collections"]:
            date_str = entry["date"]
            collection_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            if collection_date < today:
                continue

            bin_types = set()

            if "bySector" in entry and self._sector in entry["bySector"]:
                bin_types.update(entry["bySector"][self._sector])

            if "allSectors" in entry:
                bin_types.update(entry["allSectors"])

            for bin_type in sorted(bin_types):
                label = LABEL_MAP.get(bin_type, bin_type)
                icon = ICON_MAP.get(bin_type)
                entries.append(
                    Collection(
                        date=collection_date,
                        t=label,
                        icon=icon,
                    )
                )

        return entries
