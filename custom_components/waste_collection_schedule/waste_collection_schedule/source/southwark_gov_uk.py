import requests
from bs4 import BeautifulSoup
from dateutil import parser
from waste_collection_schedule import Collection

TITLE = "London Borough of Southwark"
DESCRIPTION = "Source for London Borough of Southwark waste collection."
URL = "https://www.southwark.gov.uk/"
COUNTRY = "uk"
TEST_CASES = {
    "Test_001": {"uprn": "200003455089"},
    "Test_002": {"uprn": "200003379615"},
}
HEADERS = {"user-agent": "Mozilla/5.0"}
ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Recycling Sack": "mdi:recycle",
    "Food Waste": "mdi:food-apple",
    "Communal Food": "mdi:food-apple",
}
NAME_MAP = {
    "Refuse": "General Waste",
    "Communal Food": "Food Waste",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.",
}

API_URL = "https://services.southwark.gov.uk/bins/lookup/"


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):
        url = f"{API_URL}{self._uprn}"

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10,
        )

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        entries = []

        for block in soup.find_all("div", class_="binProduct"):
            # Get bin type, ignore accessibility text
            title_tag = block.select_one("p.h3:not(.hide-for-sr)")
            if not title_tag:
                continue

            bin_type = title_tag.get_text(strip=True)
            bin_type = bin_type.removesuffix(" Collection").strip()
            bin_type = NAME_MAP.get(bin_type, bin_type)

            # Get next collection date, ignore 'Last collection:' text
            next_tag = block.find("p", string=lambda x: x and "Next collection:" in x)
            if not next_tag:
                continue

            date_text = next_tag.text.replace("Next collection:", "").strip()
            date = parser.parse(date_text).date()

            entries.append(
                Collection(
                    date=date,
                    t=bin_type,
                    icon=ICON_MAP.get(bin_type, "mdi:trash-can"),
                )
            )
        return entries
