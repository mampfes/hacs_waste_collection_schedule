from typing import Optional

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Windsor and Maidenhead"
DESCRIPTION = "Source for Windsor and Maidenhead."
URL = "https://my.rbwm.gov.uk/"
TEST_CASES = {
    "Windsor 1": {"postcode": "SL4 4EN", "uprn": 100080381393},
    "Windsor 2": {"postcode": "", "uprn": "100080384194"},
    "Maidenhead 1": {"uprn": "100080359672"},
    "Maidenhead 2": {"uprn": 100080355442},
}


ICON_MAP = {
    "refuse": "mdi:trash-can",
    "garden waste": "mdi:leaf",
    "recycling": "mdi:recycle",
}

PARAM_TRANSLATIONS = {
    "de": {
        "postcode": "(Leer lassen)",
        "uprn": "UPRN",
    },
    "en": {
        "postcode": "(Leave Empty)",
        "uprn": "UPRN",
    },
    "it": {
        "postcode": "(Lascia vuoto)",
        "uprn": "UPRN",
    },
}

API_URL = "https://forms.rbwm.gov.uk/bincollections"


HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
}


class Source:
    # postcode was previously required by this source. This is no longer the case but argument kept for backwards compatibility
    def __init__(self, uprn: str | int, postcode: Optional[str] = None):
        self._uprn: str = str(uprn).zfill(12)

    def fetch(self):
        s = requests.Session()
        r = s.get(API_URL, params={"uprn": self._uprn})
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        table = soup.find("table")
        if table is None:
            raise Exception("No results found. UPRN may be incorrect.")

        entries = []
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) != 2:
                continue

            bi_type = tds[0].text.split("Collection Service")[0].strip()
            date_string = tds[1].text.strip()
            date = parse(date_string).date()
            icon = ICON_MAP.get(bi_type.lower())  # Collection icon
            entries.append(Collection(date=date, t=bi_type, icon=icon))

        return entries
