from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "?????"
DESCRIPTION = (
    "Consolidated waste collection provider for several districts in Lower Austria"
)
URL = "https://www.umweltverbaende.at/"
EXTRA_INFO = [
    {
        "title": "GVA Lilienfeld",
        "url": "https://lilienfeld.umweltverbaende.at/",
        "country": "at",
    },
    {"title": "GV Krems", "url": "https://krems.umweltverbaende.at/", "country": "at"},
    {"title": "GVA Tulln", "url": "https://tulln.umweltverbaende.at/", "country": "at"},
    {
        "title": "Abfallverband Korneuburg",
        "url": "https://korneuburg.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "GVU Scheibbs",
        "url": "https://scheibbs.umweltverbaende.at/",
        "country": "at",
    },
    {"title": "GV Gmünd", "url": "https://gmuend.umweltverbaende.at/", "country": "at"},
    {
        "title": "GVU St. Pölten",
        "url": "https://stpoeltenland.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "GVA Mödling",
        "url": "https://moedling.umweltverbaende.at/",
        "country": "at",
    },
    {"title": "GVU Melk", "url": "https://melk.umweltverbaende.at/", "country": "at"},
    {
        "title": "GV Zwettl",
        "url": "https://zwettl.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "Gemeindeverband Horn",
        "url": "https://horn.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "Abfallverband Hollabrunn",
        "url": "https://hollabrunn.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "GDA Amstetten",
        "url": "https://amstetten.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "GAUM Mistelbach",
        "url": "https://mistelbach.umweltverbaende.at/",
        "country": "at",
    },
    {"title": "GVA Baden", "url": "https://baden.umweltverbaende.at/", "country": "at"},
]
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
    def __init__(self, district, municipal):
        self._district = district
        self._municipal = municipal

    def fetch(self):
        s = requests.Session()

        # Select appropriate url
        for item in EXTRA_INFO:
            if self._district in item["url"]:
                url = item["url"]

        # get list of municipalities and weblinks
        r0 = s.get(f"{url}?kat=32")
        soup = BeautifulSoup(r0.text, "html.parser")
        table = soup.find_all("div", {"class": "col-sm-9"})
        entries = []
        for item in table:
            weblinks = item.find_all("a", {"class": "weblink"})
            for item in weblinks:
                # match weblink with municipalities to get collection schedule
                if self._district in item.text:
                    r1 = s.get(f"{url}{item['href']}")
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
