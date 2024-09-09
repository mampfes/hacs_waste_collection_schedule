import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse

from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Islington Council"
DESCRIPTION = "Source for Islington Council, UK."
URL = "https://www.islington.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "5300094897"},
    "Test_002": {"uprn": "10001295652"},
}
ICON_MAP = {
    "Green recycling box": "mdi:recycle",
    "Dry recycling bin": "mdi:recycle",
    "Communal dry recycling bin": "mdi:recycle",
    "Small kitchen waste box": "mdi:food",
    "Large brown kitchen waste box": "mdi:food",
    "Reuseable garden waste sack": "mdi:leaf",
    "Household refuse sack": "mdi:trash-can",
    "Refuse skip": "mdi:trash-can",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)
        self._session = requests.Session()

    def fetch(self):
        url = f"https://www.islington.gov.uk/your-area?Postcode=unused&Uprn={self._uprn}"
        response = self._session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        entries = []

        waste_table = (
            soup.find(string="Waste and recycling collections")
            .find_next("div", class_="m-toggle-content")
            .find("table")
        )

        if waste_table:
            rows = waste_table.find_all("tr")
            for row in rows:
                waste_type = row.find("th").text.strip()
                collection_day = row.find("td").text.strip()

                entries.append(
                    Collection(
                        date=parse(collection_day).date(),
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )

        return entries
