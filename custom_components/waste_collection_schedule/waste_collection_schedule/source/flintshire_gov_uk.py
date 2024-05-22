import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Flintshire"
DESCRIPTION = "Source for Flintshire, United Kingdom."
URL = "https://flintshire.gov.uk/"
TEST_CASES = {
    "100100211557": {"uprn": 100100211557},
    "200001744973": {"uprn": "200001744973"},
}


ICON_MAP = {
    "Trash": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Bio": "mdi:leaf",
    "Paper": "mdi:package-variant",
    "Recycle": "mdi:recycle",
}


API_URL = "https://digital.flintshire.gov.uk/FCC_BinDay/Home/Details2/{UPRN}"


class Source:
    def __init__(self, uprn: str | int):
        self._url = API_URL.format(UPRN=uprn)

    def fetch(self):
        r = requests.post(self._url)
        if r.status_code == 500:
            raise Exception("web request failed: probably caused by an invalid UPRN")
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        rows = soup.find_all("div", class_="col-md-12")
        entries = []

        for row in rows:
            cols = row.find_all("div")
            cols = list(map(lambda x: x.text.strip(), cols))
            if len(cols) == 0 or not re.match(r"\d{2}/\d{2}/\d{4}", cols[0]):
                continue

            date_str = cols[0]
            date = datetime.strptime(date_str, "%d/%m/%Y").date()

            waste_types = cols[2].split("/")

            for waste_type in waste_types:
                icon = ICON_MAP.get(waste_type.lower().strip())  # Collection icon
                type = waste_type.strip()
                entries.append(Collection(date=date, t=type, icon=icon))

        return entries
