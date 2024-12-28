from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Oldham Council"
DESCRIPTION = "Source for Oldham Council."
URL = "https://oldham.gov.uk/"
TEST_CASES = {
    "Test_001": {"uprn": 422000125973},
    "Test_002": {"uprn": "422000129104"},
    "Test_003": {"uprn": 422000042299},
}
ICON_MAP = {
    "Brown": "mdi:recycle",
    "Green": "mdi:leaf",
    "Grey": "mdi:trash-can",
    "Blue": "mdi:newspaper",
}
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "an easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.",
}

PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn)

    def fetch(self):
        s = requests.session()
        r = s.get(
            f"https://portal.oldham.gov.uk/bincollectiondates/details?uprn={self._uprn}"
        )
        r.raise_for_status

        soup = BeautifulSoup(r.content, "html.parser")
        pickups: list = soup.find_all("table", {"class": "data-table confirmation"})

        entries: list = []
        for item in pickups:
            w: str = item.find("th")
            d: str = item.find("td", {"class": "coltwo"})
            entries.append(
                Collection(
                    date=datetime.strptime(d.text.strip(), "%d/%m/%Y").date(),
                    t=w.text.strip(),
                    icon=ICON_MAP.get(w.text.strip()),
                )
            )

        return entries
