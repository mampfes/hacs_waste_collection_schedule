from datetime import datetime

import requests
from bs4 import BeautifulSoup, NavigableString
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Windsor and Maidenhead"
DESCRIPTION = "Source for Windsor and Maidenhead."
URL = "https://my.rbwm.gov.uk/"
TEST_CASES = {
    "Windsor 1": {"uprn": 100080381393},
    "Windsor 2": {"uprn": "100080384194"},
    "Maidenhead 1": {"uprn": "100080359672"},
    "Maidenhead 2": {"uprn": 100080355442},
}


ICON_MAP = {
    "refuse": "mdi:trash-can",
    "garden waste": "mdi:leaf",
    "recycling": "mdi:recycle",
}


API_URL = "https://my.rbwm.gov.uk/special/your-collection-dates"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str = str(uprn).zfill(12)

    def fetch(self):
        s = requests.Session()
        args = {
            "uprn": self._uprn,
            "subdate": datetime.now().strftime("%Y-%m-%d"),
        }

        # request needs to be made twice to get the correct response
        r = s.get(API_URL, params=args)
        r.raise_for_status()

        r = s.get(API_URL, params=args)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        table = soup.find("table")

        if not table or isinstance(table, NavigableString):
            raise Exception("Invalid response from API")

        entries = []
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) != 2:
                continue

            bi_type = tds[0].text.split("Collection Service")[0].strip()

            date_string = tds[1].text.strip()

            date = datetime.strptime(date_string, "%d/%m/%Y").date()
            icon = ICON_MAP.get(bi_type.lower())  # Collection icon
            entries.append(Collection(date=date, t=bi_type, icon=icon))

        return entries
