from datetime import datetime

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Gwynedd"
DESCRIPTION = "Source for Gwynedd."
URL = "https://www.gwynedd.gov.uk/"
TEST_CASES = {
    "200003177805": {"uprn": 200003177805},
    "200003175227": {"uprn": "200003175227"},
    "10070340900": {"uprn": 10070340900},
}


ICON_MAP = {
    "brown": "mdi:leaf",
    "green": "mdi:trash-can",
    "blue": "mdi:recycle",
}


API_URL = "https://diogel.gwynedd.llyw.cymru/Daearyddol/en/LleDwinByw/Index/{uprn}"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def fetch(self):
        r = requests.get(API_URL.format(uprn=self._uprn))
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        collections_headline = soup.find("h6", text="Next collection dates:")
        if not isinstance(collections_headline, Tag):
            raise Exception("Could not find collections")
        collections = collections_headline.find_next("ul").find_all("li")

        entries = []

        for collection in collections:
            if not isinstance(collection, Tag):
                continue
            for p in collection.find_all("p"):
                p.extract()

            bin_type, date_str = collection.text.strip().split(":")[:2]
            bin_type, date_str = bin_type.strip(), date_str.strip()

            date = datetime.strptime(date_str, "%A %d/%m/%Y").date()
            icon = ICON_MAP.get(bin_type.split(" ")[0].lower())  # Collection icon
            entries.append(Collection(date=date, t=bin_type, icon=icon))

        return entries
