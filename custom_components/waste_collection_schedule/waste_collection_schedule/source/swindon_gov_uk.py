import requests
from bs4 import BeautifulSoup
from dateutil import parser
from waste_collection_schedule import Collection

TITLE = "Swindon Borough Council"
DESCRIPTION = "Swindon Borough Council, UK - Waste Collection"
URL = "https://www.swindon.gov.uk"
TEST_CASES = {
    "1 Nyland Road": {"uprn": "100121147490"},
    "74 Standen Way": {"uprn": "200002922415"},
    "1 Eastbury Way": {"uprn": "10010424600"},
    "33 Ulysses Road": {"uprn": "10010427033"},
}

ICON_MAP = {
    "Rubbish bin": "mdi:trash-can",
    "Recycling boxes": "mdi:recycle",
    "Garden waste bin": "mdi:leaf",
    "Plastics": "mdi:sack",
}


class Source:
    def __init__(self, uprn: str):
        self._uprn = uprn

    def fetch(self):
        params = {"uprnSubmit": "Yes", "addressList": self._uprn}
        r = requests.post(
            "https://www.swindon.gov.uk/info/20122/rubbish_and_recycling_collection_days",
            params=params,
        )
        r.raise_for_status()

        entries = []
        for results in BeautifulSoup(r.text, "html.parser").find_all(
            "div", class_="bin-collection-content"
        ):

            try:
                recyclingdate = results.find("span", class_="nextCollectionDate")

                if recyclingdate is not None:
                    recyclingtype = results.find("div", class_="content-left").find(
                        "h3"
                    )
                    entries.append(
                        Collection(
                            date=parser.parse(recyclingdate.text, dayfirst=True).date(),
                            t=recyclingtype.text,
                            icon=ICON_MAP.get(recyclingtype.text),
                        )
                    )
            except (StopIteration, TypeError):
                pass
        return entries
