# Credit where it's due:
# This is predominantly a refactoring of the Bristol City Council script from the UKBinCollectionData repo
# https://github.com/robbrad/UKBinCollectionData

from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Shropshire Council"
DESCRIPTION = "Source for Shropshire Council."
URL = "https://shropshire.gov.uk"
TEST_CASES = {
    "100070056686": {"uprn": 100070056686},
    "200000119191": {"uprn": "200000119191"},
}


ICON_MAP = {
    "General": "mdi:trash-can",
    "Garden": "mdi:leaf",
    "Recycling": "mdi:recycle",
}


API_URL = "https://bins.shropshire.gov.uk/property/{uprn}"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def fetch(self):
        page = requests.get(API_URL.format(uprn=self._uprn))
        page.raise_for_status()

        # Make a BS4 object
        soup = BeautifulSoup(page.text, features="html.parser")
        soup.prettify()

        # Form a JSON wrapper
        entries = []

        # Find section with bins in
        sections = (
            soup.find("div", {"class": "container results-table-wrapper"})
            .find("tbody")
            .find_all("tr")
        )

        # For each bin section, get the text and the list elements
        for item in sections:
            words = item.find_next("a").text.split()[:-1]
            bin_type = " ".join(words).capitalize()
            date = (
                item.find("td", {"class": "next-service"})
                .find_next("span")
                .next_sibling.strip()
            )
            next_collection = datetime.strptime(date, "%d/%m/%Y").date()
            entries.append(
                Collection(
                    t=bin_type,
                    date=next_collection,
                    icon=ICON_MAP.get(bin_type.split(" ")[0].lower()),
                )
            )

        return entries
