from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Marktgemeinde Gössendorf"
DESCRIPTION = "Source for Marktgeneinde Gössendorf, AT"
URL = "https://www.goessendorf.com/"
TEST_CASES = {"TestSource": {}, "IgnoredArgument": {"_": ""}}
ICON_MAP = {
    "Bioabfall": "mdi:food",
    "Altpapier P1": "mdi:newspaper",
    "Altpapier P2": "mdi:newspaper",
    "Sperrmüll S1": "mdi:factory",
    "Sperrmüll S2": "mdi:factory",
    "Restmüll R1": "mdi:trash-can",
    "Restmüll R2": "mdi:trash-can",
}


class Source:
    def __init__(self, _=None):
        pass

    def fetch(self):
        s = requests.Session()
        r = s.get("https://www.goessendorf.com/system/web/kalender.aspx")

        soup = BeautifulSoup(r.text, "html.parser")
        div = soup.find(
            id="ctl00_ctl00_ctl00_cph_col_a_cph_content_cph_content_list_style")

        dts = div.find_all("h2")
        ul = div.find_all("ul")[1::]
        wst = ''

        entries = []
        for i in range(0, len(dts)):
            wst = ul[i].find_all("a")
            for j in range(0, len(wst)):
                entries.append(
                    Collection(
                        date=datetime.strptime(
                            dts[i].text.split(" ")[0].strip(), "%d.%m.%Y"
                        ).date(),
                        t=wst[j].text.strip(),
                        icon=ICON_MAP.get(wst[j].text.strip()),
                    )
                )

        return entries
