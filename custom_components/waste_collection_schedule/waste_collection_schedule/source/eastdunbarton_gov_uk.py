from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "East Dunbartonshire Council"
DESCRIPTION = "Source for East Dunbartonshire Council, UK."
URL = "https://eastdunbarton.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "132020996"},
    "Test_002": {"uprn": 132040577},
    "Test_003": {"uprn": 132020494},
}
ICON_MAP = {
    "Food caddy": "mdi:food",
    "Green bin": "mdi:leaf",
    "Brown bin": "mdi:bottle-wine",
    "Blue bin": "mdi:recycle",
    "Grey bin": "mdi:trash-can",
}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn)

    def fetch(self):
        s = requests.Session()
        r = s.get(
            f"https://www.eastdunbarton.gov.uk/services/a-z-of-services/bins-waste-and-recycling/bins-and-recycling/collections/?uprn={self._uprn}"
        )
        r.raise_for_status
        soup = BeautifulSoup(r.content, "html.parser")

        entries = []
        trs = soup.find_all("tr")
        for tr in trs[1:]:
            tds = tr.find_all("td")
            entries.append(
                Collection(
                    date=datetime.strptime(
                        tds[1].text.strip().split(", ")[1], "%d %B %Y"
                    ).date(),
                    t=tds[0].text.strip(),
                    icon=ICON_MAP.get(tds[0].text.strip()),
                )
            )

        return entries
