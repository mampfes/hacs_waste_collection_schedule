from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Warwick District Council"
DESCRIPTION = "Source for Warwick District Council rubbish collection."
URL = "https://www.warwickdc.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "100070260258"},
    "Test_002": {"uprn": "100070258568"},
    "Test_003": {"uprn": 100070263501},
}
ICON_MAP = {
    "FOOD": "mdi:food",
    "GARDEN": "mdi:leaf",
    "RECYCLING": "mdi:recycle",
    "REFUSE": "mdi:trash-can",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        s = requests.Session()
        r = s.get(
            f"https://estates7.warwickdc.gov.uk/PropertyPortal/Property/Recycling/{self._uprn}"
        )
        soup = BeautifulSoup(r.text, "html.parser")

        infoboxes = soup.findAll(
            "div", {"class": "col-xs-12 text-center waste-dates margin-bottom-15"}
        )

        entries = []
        for box in infoboxes:
            items = box.findAll("p")
            waste_type = items[0].text.strip().split(" ")[0].strip()
            dates = [datetime.strptime(d.text, "%d/%m/%Y").date() for d in items[1:]]
            for date in dates:
                entries.append(
                    Collection(
                        date=date,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type.upper()),
                    )
                )

        return entries
