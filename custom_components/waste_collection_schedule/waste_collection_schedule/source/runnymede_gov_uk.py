from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Runnymede Borough Council"

DESCRIPTION = "Source Script for www.runnymede.gov.uk services for Runnymede Borough Council, Surrey, UK"

URL = "https://www.runnymede.gov.uk"

TEST_CASES = {
    "Acacia Close/uprn as string": {"uprn": "100061482004"},
    "Acacia Close/uprn as number": {"uprn": 100061482004},
    "Addlestone Library/uprn as string": {"uprn": "10002019806"},
    "Addlestone Library/uprn as number": {"uprn": 10002019806},
}

API_URL = "https://www.runnymede.gov.uk/bin-collection-day"


ICON_MAP = {
    "Food caddy": "mdi:food",
    "Garden waste": "mdi:leaf",
    "Recycling": "mdi:recycle",
    "Refuse": "mdi:trash-can",
}


class Source:
    def __init__(self, uprn: str):
        self._uprn = uprn

    def fetch(self):
        session = requests.Session()
        params = {"address": self._uprn}
        r = session.get(API_URL, params=params)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")
        soup.prettify()

        results = soup.find_all("tr")

        entries = []
        for result in results:
            result_row = result.find_all("td")
            if len(result_row) >= 2:
                date = datetime.strptime(result_row[1].text, "%A, %d %B %Y").date()

                collection_text = result_row[0].text.strip()
                entries.append(
                    Collection(
                        date=date,
                        t=collection_text,
                        icon=ICON_MAP.get(collection_text),
                    )
                )

        return entries
