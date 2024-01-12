import datetime
import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "City of Karlsruhe"
DESCRIPTION = "Source for City of Karlsruhe."
URL = "https://www.karlsruhe.de/"
TEST_CASES = {
    "Östliche Rheinbrückenstraße 1": {
        "street": "Östliche Rheinbrückenstraße",
        "hnr": 1
    },
    "Habichtweg 4": {
        "street": "Habichtweg", 
        "hnr": 4
    },
    "Machstraße 5": {
        "street": "Machstraße", 
        "hnr": 5
    },
    "Bernsteinstraße 10 ladeort 1": {
        "street": "Bernsteinstraße",
        "hnr": 10,
        "ladeort": 1
    },
    "Bernsteinstraße 10 ladeort 2": {
        "street": "Bernsteinstraße",
        "hnr": 10,
        "ladeort": 2
     }
}


ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Bioabfall": "mdi:leaf",
    "Papier": "mdi:package-variant",
    "Wertstoff": "mdi:recycle",
    "Sperrmüllabholung": "mdi:wardrobe"
}


API_URL = "https://web6.karlsruhe.de/service/abfall/akal/akal_2024.php"


class Source:
    def __init__(self, street: str, hnr: str | int, ladeort: int | None = None):
        self._street: str = street
        self._hnr: str | int = hnr
        self._ladeort: int | None = ladeort

    def fetch(self):
        args = {
            "strasse_n": self._street,
            "hausnr": self._hnr,
            "ladeort": self._ladeort,
            "anzeigen": "anzeigen"
        }

        # get html file
        r = requests.post(API_URL, data=args, params={"hausnr=": ""})
        r.raise_for_status()

        with open("test.html", "w", encoding="utf-8") as f:
            f.write(r.text)

        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.find_all("div", class_="row")
        entries = []

        for row in rows:
            column = row.find("div", class_="col_6-2")
            
            if column is None or not column.contents:
                column = row.find("div", class_="col_7-3")
                if column is None or not column.contents:
                    continue

                for content in column.contents:
                    if content.text.startswith("Sperrmüllabholung"):
                        bin_type = column.contents[0].text.strip()
                        if bin_type.endswith(":"):
                            bin_type = bin_type[:-1].strip()
                        icon = ICON_MAP.get(bin_type)  # Collection icon

                    elif content.text.startswith("Straßensperrmüll"):
                        dates = re.findall(r"\d{2}\.\d{2}\.\d{4}", content.text)
                        date = datetime.datetime.strptime(dates[0], "%d.%m.%Y").date()

                entries.append(Collection(date=date, t=bin_type, icon=icon))

            else:
                bin_type = column.contents[0].text.split(",")[0].strip()
                icon = ICON_MAP.get(bin_type)  # Collection icon

                pickup_col = row.find("div", class_="col_6-3")
                if pickup_col is None or not pickup_col.contents:
                    continue

                for date in re.findall(r"\d{2}\.\d{2}\.\d{4}", pickup_col.text):
                    date = datetime.datetime.strptime(date, "%d.%m.%Y").date()
                    entries.append(Collection(date=date, t=bin_type, icon=icon))

        return entries
