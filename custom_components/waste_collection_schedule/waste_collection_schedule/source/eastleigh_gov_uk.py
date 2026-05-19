from datetime import datetime

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Eastleigh Borough Council"
DESCRIPTION = "Source for Eastleigh Borough Council."
URL = "https://eastleigh.gov.uk"
TEST_CASES = {
    "100060319000": {"uprn": 100060319000},
    "100060300958": {"uprn": "100060300958"},
}


ICON_MAP = {
    "Paper": Icons.PAPER,
    "household": Icons.GENERAL_WASTE,
    "recycling": Icons.RECYCLING,
    "food": Icons.BIO_KITCHEN,
    "glass": Icons.GLASS,
    "garden": Icons.GARDEN,
}


API_URL = "https://eastleigh.gov.uk/waste-bins-and-recycling/collection-dates/your-waste-bin-and-recycling-collections"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def fetch(self):
        session = requests.Session(impersonate="chrome124")
        args = {"uprn": self._uprn}

        # get json file
        r = session.get(API_URL, params=args)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        dls = soup.find_all("dl")

        entries = []

        for dl in dls:
            dts = dl.findAll("dt")
            for dt in dts:
                dd = dt.find_next_sibling("dd")
                if not dd:
                    continue

                try:
                    # Mon, 29 Apr 2024
                    date = datetime.strptime(dd.text, "%a, %d %b %Y").date()
                except ValueError:
                    continue

                icon = ICON_MAP.get(
                    dt.text.strip().split(" ")[0].lower()
                )  # Collection icon
                type = dt.text
                entries.append(Collection(date=date, t=type, icon=icon))

        return entries
