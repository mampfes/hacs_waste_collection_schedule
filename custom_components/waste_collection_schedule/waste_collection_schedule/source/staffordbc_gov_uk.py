from datetime import datetime
import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Stafford Borough Council"
DESCRIPTION = "Source for bin collection services for Stafford Borough Council, UK."
URL = "https://www.staffordbc.gov.uk/"
TEST_CASES = {
    "domestic": {"uprn": "100031780029"},
}

API_URL = "https://www.staffordbc.gov.uk/address/"

ICON_MAP = {
    "Blue bin": "mdi:recycle",
    "Brown bin": "mdi:leaf",
    "Green bin": "mdi:trash-can",
}


class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self):
        req = requests.get(
            f"https://www.staffordbc.gov.uk/address/{self._uprn}"
        )

        soup = BeautifulSoup(req.content, "html.parser")

        greenbin = soup.find_all('td')[5]
        bluebin = soup.find_all('td')[7]

        entries = [Collection(
            date=datetime.strptime(greenbin.text.strip(), "%a %d %b %Y").date(),  # Collection date
            t="Green Bin",  # Collection type
            icon=ICON_MAP.get("Green bin"),  # Collection icon
        ), Collection(
            date=datetime.strptime(bluebin.text.strip(), "%a %d %b %Y").date(),  # Collection date
            t="Blue Bin",  # Collection type
            icon=ICON_MAP.get("Blue bin"),  # Collection icon
        )]  # List that holds collection schedule

        return entries
