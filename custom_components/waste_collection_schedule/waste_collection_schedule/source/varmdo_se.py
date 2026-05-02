import re
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Värmdö Sophämtning"
DESCRIPTION = "Source for Värmdö household waste collection."
URL = "https://www.varmdo.se"
COUNTRY = "se"

SCHEDULE_URL = "https://www.varmdo.se/byggabomiljo/avfallochatervinning/alltomavfallochatervinning/avfallshamtning/hamtveckoravfallfastlandet.4.4fd26e29194d31bcc1fa6ed.html"

TEST_CASES = {
    "Rosenmalmsvägen": {"street_address": "Rosenmalmsvägen"},
    "Abborrberget": {"street_address": "Abborrberget"},
    "Idskäret": {"street_address": "Idskäret"},
}

ICON_MAP = {
    "Trash": "mdi:trash-can",
}

WEEKDAY_MAP = {
    "måndag": 0,
    "tisdag": 1,
    "onsdag": 2,
    "torsdag": 3,
    "fredag": 4,
    "lördag": 5,
    "söndag": 6,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your street name as shown on the Värmdö kommun waste collection page.",
}

PARAM_TRANSLATIONS = {
    "en": {
        "street_address": "Street Address",
    },
}


class Source:
    def __init__(self, street_address: str):
        self._street_address = re.sub(r"\d+", "", street_address).strip()

    def fetch(self) -> list[Collection]:
        response = requests.get(SCHEDULE_URL, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        cell = soup.find("td", string=re.compile(self._street_address, re.I))

        if not cell:
            raise SourceArgumentNotFound("street_address", self._street_address)

        row = cell.parent
        weekday_text = row.find_all("td")[1].text.strip().lower()

        if not weekday_text:
            raise SourceArgumentNotFound("street_address", self._street_address)

        # Determine collection weekday
        pickup_weekday = 0
        for name, idx in WEEKDAY_MAP.items():
            if name in weekday_text:
                pickup_weekday = idx
                break

        # Determine even/odd week collection
        even_weeks = "jämna" in weekday_text

        # Generate upcoming collection dates
        entries = []
        current = date.today()

        for _ in range(10):
            while (
                current.weekday() != pickup_weekday
                or (current.isocalendar()[1] % 2 == 0) != even_weeks
            ):
                current += timedelta(days=1)

            entries.append(
                Collection(
                    date=current,
                    t="Trash",
                    icon=ICON_MAP.get("Trash"),
                )
            )
            current += timedelta(days=1)

        return entries
