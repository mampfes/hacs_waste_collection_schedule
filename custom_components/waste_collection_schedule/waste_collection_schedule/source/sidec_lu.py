import re
from datetime import date, datetime

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)

TITLE = "SIDEC"
DESCRIPTION = "Source for SIDEC waste collection."
URL = "https://www.sidec.lu"
TEST_CASES = {
    "Parc Hosingen": {"commune": "Parc Hosingen (36777)"},
    "Mersch": {"commune": "Mersch (2611)"},
    "Invalid Commune": {"commune": "Invalid (12345)"},
}

# Yearly collection data used by the calendar on the SIDEC homepage.
API_URL = "https://sidec.lu/collectes/{year}.json"
ICON_MAP = {
    "BULKY": Icons.BULKY,
    "GLASS": Icons.GLASS,
    "ORGANIC": Icons.ORGANIC,
    "PAPER": Icons.PAPER,
    "RESIDUAL": Icons.GENERAL_WASTE,
}

WASTE_MAPPING = {
    "encombrants": "BULKY",
    "verre": "GLASS",
    "bio": "ORGANIC",
    "papier": "PAPER",
    "menager": "RESIDUAL",
}


class Source:
    def __init__(self, commune: str | None = None):
        self._commune = commune
        # Older configurations use "Name (id)" from the previous website;
        # the commune name alone identifies the commune now.
        self._commune_name = (
            re.sub(r"\s*\(\d+\)\s*$", "", commune).strip() if commune else None
        )

    def _fetch_year(self, year: int) -> dict | None:
        r = requests.get(API_URL.format(year=year))
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()["communes"]

    def fetch(self):
        now = datetime.now()
        communes = self._fetch_year(now.year)
        if communes is None:
            raise Exception(f"No SIDEC collection data published for {now.year}.")

        if not self._commune_name:
            raise SourceArgumentRequiredWithSuggestions(
                "commune", None, sorted(communes)
            )
        if self._commune_name not in communes:
            raise SourceArgumentNotFoundWithSuggestions(
                "commune", self._commune, sorted(communes)
            )

        collections = self._collections(communes[self._commune_name])

        # next year's data is published towards the end of the year
        if now.month >= 10:
            next_year = self._fetch_year(now.year + 1)
            if next_year and self._commune_name in next_year:
                collections.extend(self._collections(next_year[self._commune_name]))

        return collections

    @staticmethod
    def _collections(commune: dict) -> list[Collection]:
        collections = []
        for key, waste_type in WASTE_MAPPING.items():
            for date_str in commune.get(key, []):
                collections.append(
                    Collection(
                        date=date.fromisoformat(date_str),
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )
        return collections
