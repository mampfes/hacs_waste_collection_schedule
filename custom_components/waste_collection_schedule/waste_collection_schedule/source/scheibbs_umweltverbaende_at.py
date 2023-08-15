from bs4 import BeautifulSoup
from datetime import datetime
import requests
from waste_collection_schedule import Collection

TITLE = "GVU Scheibbs"
DESCRIPTION = (
    "Source for waste collection services Association of Municipalities in the District of Scheibbs"
)
URL = "https://scheibbs.umweltverbaende.at/"
TEST_CASES = {
    "Test_001": {"region": "Gaming"},
    "Test_002": {"region": "Sankt Anton an der Jeßnitz"},
    "Test_003": {"region": "Göstling an der Ybbs"},
    "Test_004": {"region": "Wieselburg"},
}
ICON_MAP = {
    "Mixed recycling and food waste": "mdi:recycle",
    "Refuse and food waste": "mdi:trash-can",
}


class Source:
    def __init__(self, region):
        self._region = region

    def fetch(self):
        s = requests.Session()
        # get list of regions and weblinks
        r0 = s.get("https://scheibbs.umweltverbaende.at/?kat=32")
        soup = BeautifulSoup(r0.text, "html.parser")
        table = soup.find_all("div", {"class": "col-sm-9"})
        entries = []
        for item in table:
            weblinks = item.find_all("a", {"class": "weblink"})
            for item in weblinks:
                if self._region in item.text:
                    r1= s.get(f"https://scheibbs.umweltverbaende.at/{item['href']}")
                    soup = BeautifulSoup(r1.text, "html.parser")
                    schedule = soup.find_all("div", {"class": "tunterlegt"})
                    for item in schedule:
                        txt = item.text.strip().split("   ")  # this is not 3 space characters, the middle one is U+00a0
                        entries.append(
                            Collection(
                                date=datetime.strptime(txt[1], "%d.%m.%Y").date(),
                                t=txt[2],
                                icon=ICON_MAP.get(txt[2].upper),
                            )
                        )                        


        return entries
