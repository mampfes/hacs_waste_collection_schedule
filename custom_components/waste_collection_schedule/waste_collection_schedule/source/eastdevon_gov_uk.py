import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "East Devon District Council"
DESCRIPTION = "Source for East Devon services for East Devon District Council, UK."
URL = "https://eastdevon.gov.uk/"
TEST_CASES = {
    "Test_001": {"uprn": "010000246114"},
    "Test_002": {"uprn": "010000272679"},
}
ICON_MAP = {
    "RUBBISH": "mdi:trash-can",
    "RECYCLING AND FOOD WASTE": "mdi:recycle",
    "GREEN WASTE": "mdi:leaf",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        s = requests.Session()
        r = s.get(
            f"https://eastdevon.gov.uk/addressfinder/?qsource=UPRN&qtype=bins&term={self._uprn}"
        )

        json_data = json.loads(r.text)[0]["Results"]
        soup = BeautifulSoup(json_data, "html.parser")
        bins = soup.findAll("h2")
        dates = soup.findAll("em")

        entries = []
        for b, d in zip(bins, dates):
            # check cases where no date is given for a collection
            if d:
                entries.append(
                    Collection(
                        date=datetime.strptime(d.text, "%A%d %B %Y"
                        ).date(),
                        t=b.text.replace(" collection", "").replace("Your ", ""),
                        icon=ICON_MAP.get(b.text.replace(" collection", "").replace("Your ", "").upper()),
                    )
                )

        return entries
