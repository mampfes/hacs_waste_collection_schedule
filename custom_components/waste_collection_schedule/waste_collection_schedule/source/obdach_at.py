from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Marktgemeinde Obdach"
DESCRIPTION = "Source for Marktgeneinde Obdach, AT"
URL = "https://www.obdach.gv.at/"
TEST_CASES: dict[str, dict[str, str]] = {"TestSource": {}}
ICON_MAP = {
    "Biomüll": Icons.BIO_KITCHEN,
    "Altstoffsammelzentrum": Icons.NEWSPAPER,
    "Gelber Sack/Tonne": Icons.PLASTIC_PACKAGING,
    "Restmüll Abfuhrbereich 1": Icons.GENERAL_WASTE,
    "Restmüll Abfuhrbereich 2": Icons.GENERAL_WASTE,
}


class Source:
    def __init__(self):
        pass

    def fetch(self):
        s = requests.Session()
        r = s.get("https://www.obdach.gv.at/system/web/kalender.aspx")

        soup = BeautifulSoup(r.text, "html.parser")
        div = soup.find(
            id="ctl00_ctl00_ctl00_cph_col_a_cph_content_cph_content_list_style"
        )

        dts = div.find_all("h2")
        wst = div.find_all("span")

        entries = []
        for i in range(0, len(dts)):
            entries.append(
                Collection(
                    date=datetime.strptime(
                        dts[i].text.split(" ")[0].strip(), "%d.%m.%Y"
                    ).date(),
                    t=wst[i].text.strip()[1:-1],
                    icon=ICON_MAP.get(wst[i].text.strip()[1:-1]),
                )
            )

        return entries
