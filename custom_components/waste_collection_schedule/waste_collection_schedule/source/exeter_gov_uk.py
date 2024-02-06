import json
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Exeter City Council"
DESCRIPTION = "Source for Exeter City services for Exeter City Council, UK."
URL = "https://exeter.gov.uk/"
TEST_CASES = {
    "Test_001": {"uprn": "100040227486"},
    "Test_002": {"uprn": "10013043921"},
    "Test_003": {"uprn": 10023120282},
    "Test_004": {"uprn": 100040241022},
}
ICON_MAP = {
    "REFUSE": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GARDEN WASTE": "mdi:leaf",
    "FOOD WASTE": "mdi:food",
}
REGEX_ORDINALS = r"(?<=[0-9])(?:st|nd|rd|th)"


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        s = requests.Session()
        r = s.get(
            f"https://exeter.gov.uk/repositories/hidden-pages/address-finder/?qsource=UPRN&qtype=bins&term={self._uprn}"
        )

        json_data = json.loads(r.text)[0]["Results"]
        soup = BeautifulSoup(json_data, "html.parser")
        bins = soup.findAll("h2")
        dates = soup.findAll("h3")

        entries = []
        for b, d in zip(bins, dates):
            # check cases where no date is given for a collection
            if d and len(d.text.split(",")) > 1:
                entries.append(
                    Collection(
                        date=datetime.strptime(
                            re.compile(REGEX_ORDINALS).sub("", d.text), "%A, %d %B %Y"
                        ).date(),
                        t=b.text.replace(" collection", ""),
                        icon=ICON_MAP.get(b.text.replace(" collection", "").upper()),
                    )
                )

        return entries
