import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Salford City Council"
DESCRIPTION = "Source for bin collection services for Salford City Council, UK."
URL = "https://www.salford.gov.uk"
TEST_CASES = {
    "domestic": {"uprn": "100011404886"},
}

ICON_MAP = {
    "Domestic waste": "mdi:trash-can",
    "Blue recycling (paper and card)": "mdi:recycle",
    "Brown recycling (bottles and cans)": "mdi:glass-fragile",
    "Food and garden waste": "mdi:leaf",
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, uprn: int):
        self._uprn = uprn

    def fetch(self):
        url = "https://www.salford.gov.uk/bins-and-recycling/bin-collection-days/your-bin-collections/"
        params = {"UPRN": self._uprn}
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"}
        
        r = requests.get(url, params=params, headers=headers)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, features="html.parser")
        results = soup.find_all("div", {"class": "col-12 col-lg-6"})

        entries = []

        for result in results:
            dates = []
            for date in result.find_all("li"):
                dates.append(date.text)
            collection_type = (result.find("strong").text).replace(":", "")
            for current_date in dates:
                date = datetime.strptime(current_date, "%A %d %B %Y").date()
                entries.append(
                    Collection(
                        date=date,
                        t=collection_type,
                        icon=ICON_MAP.get(collection_type),
                    )
                )

        return entries
