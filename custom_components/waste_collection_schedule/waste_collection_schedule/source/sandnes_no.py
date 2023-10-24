# nearly identical to stavanger_no

from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Sandnes Kommune"
DESCRIPTION = "Source for Sandnes Kommune, Norway"
URL = "https://www.sandnes.kommune.no/"
TEST_CASES = {
    "TestcaseI": {
        "id": "181e5aac-3c88-4b0b-ad46-3bd246c2be2c",
        "municipality": "Sandnes kommune 2020",
        "gnumber": "62",
        "bnumber": "281",
        "snumber": "0",
    },
    "TestcaseII": {
        "id": "cb263140-1743-4459-ab3a-a9677884904f",
        "municipality": "Sandnes kommune 2020",
        "gnumber": 33,
        "bnumber": 844,
        "snumber": 0,
    },
}

ICON_MAP = {
    "Restavfall": "mdi:trash-can",
    "Papp/papir": "mdi:recycle",
    "Papir": "mdi:recycle",
    "Bio": "mdi:leaf",
    "Våtorganisk avfall": "mdi:leaf",
    "Juletre": "mdi:pine-tree",
}


class Source:
    def __init__(self, id, municipality, gnumber, bnumber, snumber):
        self._id = id
        self._municipality = municipality
        self._gnumber = gnumber
        self._bnumber = bnumber
        self._snumber = snumber

    def fetch(self):
        url = "https://www.hentavfall.no/rogaland/sandnes/tommekalender/show"

        params = {
            "id": self._id,
            "municipality": self._municipality,
            "gnumber": self._gnumber,
            "bnumber": self._bnumber,
            "snumber": self._snumber,
        }

        r = requests.get(url, params=params)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        tag = soup.find_all("option")
        year = tag[0].get("value").split("-")
        year = year[1]

        entries = []
        for tag in soup.find_all("tr", {"class": "waste-calendar__item"}):
            if tag.text.strip() == "Dato og dag\nAvfallstype":
                continue

            date = tag.text.strip().split(" - ")
            date = datetime.strptime(date[0] + "." + year, "%d.%m.%Y").date()

            for img in tag.find_all("img"):
                waste_type = img.get("title")
                entries.append(
                    Collection(date, waste_type, icon=ICON_MAP.get(waste_type))
                )

        return entries
