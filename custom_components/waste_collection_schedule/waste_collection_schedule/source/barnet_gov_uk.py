import requests
from bs4 import BeautifulSoup
from dateutil import parser
from waste_collection_schedule import Collection

TITLE = "London Borough of Barnet"  # Title will show up in README.md and info.md
DESCRIPTION = "Source script for barnet.gov.uk"  # Describe your source
URL = "https://www.barnet.gov.uk/"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {"Test_001": {"uprn": "200062903"}, "Test_002": {"uprn": "200072958"}}
HEADERS = {"user-agent": "Mozilla/5.0"}
ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling Bin": "mdi:recycle",
    "Food Waste": "mdi:food-apple",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details."
    },
    "de": {
        "uprn": "Eine einfache Möglichkeit, Ihre Unique Property Reference Number (UPRN) zu finden, besteht darin, auf https://www.findmyaddress.co.uk/ zu gehen und Ihre Adressdaten einzugeben."
    },
}

API_URL = "https://myforms.barnet.gov.uk/homepage/11/find-your-bin-collection-day"


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):
        response = requests.get(
            API_URL,
            headers=HEADERS,
            params={"address": self._uprn},
            timeout=10,
        )

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        entries = []

        bins = soup.find_all("h4", class_="bin-collection__heading")
        dates = soup.find_all("p", class_="bin-collection__date")
        for date_tag, bin_tag in zip(dates, bins, strict=True):
            date = parser.parse(date_tag.text).date()
            bin_name = bin_tag.text.strip()

            entries.append(
                Collection(
                    date=date,
                    t=bin_name,
                    icon=ICON_MAP.get(bin_name),
                )
            )

        return entries
