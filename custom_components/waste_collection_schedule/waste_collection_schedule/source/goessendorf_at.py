from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Marktgemeinde Gössendorf"
DESCRIPTION = "Source for Marktgemeinde Gössendorf, AT"
URL = "https://www.goessendorf.com/"
TEST_CASES: dict[str, dict[str, str]] = {"TestSource": {}}
ICON_MAP = {
    "Bioabfall": Icons.BIO_KITCHEN,
    "Altpapier P1": Icons.PAPER,
    "Altpapier P2": Icons.PAPER,
    "Sperrmüll S1": Icons.BULKY,
    "Sperrmüll S2": Icons.BULKY,
    "Restmüll R1": Icons.GENERAL_WASTE,
    "Restmüll R2": Icons.GENERAL_WASTE,
}


class Source:
    def __init__(self):
        pass

    def fetch(self):
        s = requests.Session()
        r = s.get("https://www.goessendorf.com/system/web/kalender.aspx")

        soup = BeautifulSoup(r.text, "html.parser")
        div = soup.find(
            id="ctl00_ctl00_ctl00_cph_col_a_cph_content_cph_content_list_style"
        )

        dts = div.find_all("h2")
        ul = div.find_all("ul")[1::]
        wst = ""

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
