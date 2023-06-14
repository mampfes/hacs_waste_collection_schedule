import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from bs4 import BeautifulSoup
import re
import datetime

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
        "hnr": "4"
    },
    "Machstraße 5": {
        "street": "Machstraße",
        "hnr": "5"
    }
}


ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Bioabfall": "mdi:leaf",
    "Papier": "mdi:package-variant",
    "Wertstoff": "mdi:recycle",
    "Sperrmüllabholung": "mdi:wardrobe"
}


API_URL = "https://web6.karlsruhe.de/service/abfall/akal/akal.php"


class Source:
    def __init__(self, street: str, hnr: str | int):
        self._street: str = street
        self._hnr: str | int = hnr

    def fetch(self):
        args = {
            "strasse_n": self._street,
            "hausnr": self._hnr,
            "anzeigen": "anzeigen",
        }

        # get json file
        r = requests.post(API_URL, data=args, params={"hausnr=": ""})
        r.raise_for_status()

        with open("test.html", "w") as f:
            f.write(r.text)

        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.find_all("div", class_="row")
        entries = []

        for row in rows:
            bin_type = row.find("div", class_="col_3-2")
            if bin_type == None:
                continue

            bin_type = bin_type.contents[0].text.split(",")[0].strip()
            if bin_type.endswith(":"):
                bin_type = bin_type[:-1].strip()

            pickup_col = row.find("div", class_="col_3-3")
            if pickup_col == None or not pickup_col.contents:
                pickup_col = row.find("div", class_="col_4-3")

                if pickup_col == None or not pickup_col.contents:
                    continue

            for date in re.findall(r"\d{2}\.\d{2}\.\d{4}", pickup_col.text):
                date = datetime.datetime.strptime(date, "%d.%m.%Y").date()

                icon = ICON_MAP.get(bin_type)  # Collection icon
                entries.append(Collection(date=date, t=bin_type, icon=icon))
        return entries
