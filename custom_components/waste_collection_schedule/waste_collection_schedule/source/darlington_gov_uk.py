from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Darlington Borough Council"
DESCRIPTION = "Source for Darlington Borough Council."
URL = "https://darlington.gov.uk"
TEST_CASES = {
    "10013321444": {"uprn": 10013321444},
    "010013315817": {"uprn": 10013315817},
    "100110560916": {"uprn": 100110560916},
    "200002724471": {"uprn": "200002724471"},
}

ICON_MAP = {
    "Food waste": Icons.ORGANIC,
    "Recycling": Icons.RECYCLING,
    "Refuse": Icons.GENERAL_WASTE,
    "Garden Waste": Icons.GARDEN,
}


API_URL = (
    "https://www.darlington.gov.uk/bins-waste-and-recycling/collection-day-lookup/"
)


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn)

    def fetch(self) -> list[Collection]:
        r = requests.get(API_URL, params={"uprn": self._uprn}, timeout=20)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        entries = []

        cards = soup.select("div.refuse-results")

        for card in cards:
            date_element = card.select_one(".collectionDate p")
            if not date_element:
                continue

            date_str = date_element.get_text(strip=True).split("(")[0].strip()
            collection_date = datetime.strptime(
                date_str,
                "%A %d %B %Y",
            ).date()
            waste_types = [
                x.get_text(strip=True) for x in card.select(".collection-result-text")
            ]

            for waste_type in waste_types:
                entries.append(
                    Collection(
                        date=collection_date,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )

        return entries
