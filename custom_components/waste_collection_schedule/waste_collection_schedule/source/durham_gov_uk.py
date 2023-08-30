from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Durham County Council"
DESCRIPTION = "Source for Durham County Council, UK."
URL = "https://durham.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "100110414978"},
    "Test_002": {"uprn": 100110427200},
}
ICON_MAP = {"RECYCLE": "mdi:recycle", "GARDEN": "mdi:leaf", "RUBBISH": "mdi:trash-can"}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn)

    def fetch(self):
        s = requests.Session()
        r = s.get(f"https://www.durham.gov.uk/bincollections?uprn={self._uprn}")
        soup = BeautifulSoup(r.text, "html.parser")

        entries = []
        for waste in ICON_MAP:
            w = soup.find_all("tr", {"class": f"{waste.lower()}"})
            for item in w:
                x = item.find_all("td")
                entries.append(
                    Collection(
                        date=datetime.strptime(x[-1].text, "%d %B %Y").date(),
                        t=x[0].text,
                        icon=ICON_MAP.get(waste),
                    )
                )

        return entries
