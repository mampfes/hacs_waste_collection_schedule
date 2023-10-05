from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "GVA Mistelbach"
DESCRIPTION = "Source for waste collection services Association of Municipalities in the District of Mistelbach"
URL = "https://mistelbach.umweltverbaende.at/"
TEST_CASES = {
    "Test_001": {"region": "Altlichtenwarth"},
    "Test_002": {"region": "Asparn an der Zaya"},
    "Test_003": {"region": "Bernhardsthal"},
    "Test_004": {"region": "Bockfließ"},
    "Test_005": {"region": "Drasenhofen"},
    "Test_006": {"region": "Falkenstein"},
    "Test_007": {"region": "Gaweinstal"},
    "Test_008": {"region": "Großebersdorf"},
    "Test_009": {"region": "Großkrut"},
    "Test_010": {"region": "Hausbrunn"},
    "Test_011": {"region": "Herrnbaumgarten"},
    "Test_012": {"region": "Kreuttal"},
    "Test_013": {"region": "Kreuzstetten"},
    "Test_014": {"region": "Ladendorf"},
    "Test_015": {"region": "Mistelbach"},
    "Test_016": {"region": "Niederleis"},
    "Test_017": {"region": "Ottenthal"},
    "Test_018": {"region": "Pillichsdorf"},
    "Test_019": {"region": "Poysdorf"},
    "Test_020": {"region": "Rabensburg"},
    "Test_021": {"region": "Schrattenberg"},
    "Test_022": {"region": "Wilfersdorf"},
    "Test_023": {"region": "Wolkersdorf im Weinviertel"},
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
        s = requests.Session()
        # get list of regions and weblinks
        r0 = s.get("https://mistelbach.umweltverbaende.at/?kat=32")
        soup = BeautifulSoup(r0.text, "html.parser")
        table = soup.find_all("div", {"class": "col-sm-9"})
        entries = []
        for item in table:
            weblinks = item.find_all("a", {"class": "weblink"})
            for item in weblinks:
                # match weblink with region to get collection schedule
                if self._region in item.text:
                    r1 = s.get(f"https://mistelbach.umweltverbaende.at/{item['href']}")
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
