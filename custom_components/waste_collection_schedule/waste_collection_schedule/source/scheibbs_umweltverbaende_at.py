import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

_LOGGER = logging.getLogger(__name__)

TITLE = "GVU Scheibbs"
DESCRIPTION = "Source for waste collection services Association of Municipalities in the District of Scheibbs"
URL = "https://scheibbs.umweltverbaende.at/"
TEST_CASES = {
    "Test_001": {"region": "Gaming"},
    "Test_002": {"region": "Sankt Anton an der Jeßnitz"},
    "Test_003": {"region": "Göstling an der Ybbs"},
    "Test_004": {"region": "Wieselburg"},
}
ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Gelber Sack": "mdi:sack",
    "Altpapier": "mdi:package-variant",
    "Biotonne": "mdi:leaf",
}


class Source:
    def __init__(self, region):
        self._region = region

    def fetch(self):
        _LOGGER.warning(
            "The scheibbs_umweltverbaende_at source is depreciated and may be removed in the future. Please migrate to the umweltverbaende_at source"
        )
        s = requests.Session()
        # get list of regions and weblinks
        r0 = s.get("https://scheibbs.umweltverbaende.at/?kat=32")
        soup = BeautifulSoup(r0.text, "html.parser")
        table = soup.find_all("div", {"class": "col-sm-9"})
        entries = []
        for item in table:
            weblinks = item.find_all("a", {"class": "weblink"})
            for item in weblinks:
                # match weblink with region to get collection schedule
                if self._region in item.text:
                    r1 = s.get(f"https://scheibbs.umweltverbaende.at/{item['href']}")
                    soup = BeautifulSoup(r1.text, "html.parser")
                    schedule = soup.find_all("div", {"class": "tunterlegt"})
                    for day in schedule:
                        txt = day.text.strip().split(" \u00a0 ")
                        entries.append(
                            Collection(
                                date=datetime.strptime(txt[1], "%d.%m.%Y").date(),
                                t=txt[2],
                                icon=ICON_MAP.get(txt[2]),
                            )
                        )

        return entries
