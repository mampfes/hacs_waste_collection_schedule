import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Kumberg"
DESCRIPTION = "Source for Kumberg."
URL = "https://www.kumberg.gv.at"
TEST_CASES: dict[str, dict] = {"Whole Kumberg": {}}


ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Bio": "mdi:leaf",
    "Papier": "mdi:package-variant",
    "Gelber Sack": "mdi:recycle",
    "Sperrmüll": "mdi:sofa",
}


API_URL = "https://www.kumberg.gv.at/kalender/"


class Source:
    def __init__(self):
        self._ics_urls = set[str]()
        self._ics = ICS()

    def _first_setup(self):
        r = requests.get(API_URL)
        soup = BeautifulSoup(r.text, "html.parser")
        cal_icons = soup.select("i.fa-calendar-plus")
        for icon in cal_icons:
            if "abfalltyp" in icon.parent["href"]:
                self._ics_urls.add(icon.parent["href"])

    def fetch(self) -> list[Collection]:
        if not self._ics_urls:
            self._first_setup()

        collections = []
        for ics_url in self._ics_urls:
            r = requests.get(ics_url)
            for date_, bin_type in self._ics.convert(r.text):
                # remove time like "7.00 - 9.30 Uhr" from bin_type
                if re.search(r"\d{1,2}\.\d{2} - \d{1,2}\.\d{2} Uhr", bin_type):
                    bin_type = re.sub(
                        r"\d{1,2}\.\d{2} - \d{1,2}\.\d{2} Uhr", "", bin_type
                    ).strip()

                icon = ICON_MAP.get(bin_type)
                collections.append(Collection(date_, bin_type, icon))
        return collections
