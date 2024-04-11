from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Marktgemeinde Edlitz"
DESCRIPTION = "Source for Marktgeneinde Edlitz, AT"
URL = "https://edlitz.at"
TEST_CASES = {"TestSource": {}, "IgnoredArgument": {"_": ""}}
ICON_MAP = {
    "Biomüllabfuhr": "mdi:food",
    "Papier Tonne": "mdi:newspaper",
    "Grüne Tonne": "mdi:recycle",
    "Restmüll": "mdi:trash-can",
    "Restmüll mit Panoramastraße": "mdi:trash-can",
}


class Source:
    def __init__(self, _=None):
        pass

    def fetch(self):
        s = requests.Session()
        r = s.get("https://www.edlitz.at/Buergerservice/Muellabfuhrtermine")

        soup = BeautifulSoup(r.text, "html.parser")
        td = soup.find_all("td", {"class": "td_kal"})

        dts = td[::2]
        wst = td[1::2]

        entries = []
        for i in range(0, len(dts)):
            entries.append(
                Collection(
                    date=datetime.strptime(
                        dts[i].text.split(" ")[0].strip(), "%d.%m.%Y"
                    ).date(),
                    t=wst[i].text.strip(),
                    icon=ICON_MAP.get(wst[i].text.strip()),
                )
            )

        return entries
