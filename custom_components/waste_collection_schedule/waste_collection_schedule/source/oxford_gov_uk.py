import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Oxford City Council"
DESCRIPTION = "Source for oxford.gov.uk services for Oxford, UK."
URL = "https://oxford.gov.uk"
TEST_CASES = {
    "Magdalen Road": {"uprn": "100120827594", "postcode": "OX4 1RB"},
    "Oliver Road (brown bin too)": {"uprn": "100120831804", "postcode": "OX4 2JH"},
}
HEADERS = {"user-agent": "Mozilla/5.0"}
API_URL = "https://www.oxford.gov.uk/xfp/form/142"

ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden": "mdi:leaf",
    "Food": "mdi:food-apple",
}


class Source:
    def __init__(self, uprn: str, postcode: str):
        self._uprn = uprn
        self._postcode = postcode

    def fetch(self):
        entries: list[Collection] = []
        session = requests.Session()

        form_landing_response = session.get(API_URL, headers=HEADERS)
        soup = BeautifulSoup(form_landing_response.text, "html.parser")
        token = soup.find("input", {"name": "__token"}).attrs["value"]
        if not token:
            raise ValueError(
                "Could not parse CSRF Token from initial response. Won't be able to proceed."
            )

        form_data = {
            "__token": token,
            "page": "12",
            "locale": "en_GB",
            "q6ad4e3bf432c83230a0347a6eea6c805c672efeb_0_0": self._postcode,
            "q6ad4e3bf432c83230a0347a6eea6c805c672efeb_1_0": self._uprn,
            "next": "Next",
        }

        collection_response = session.post(API_URL, data=form_data, headers=HEADERS)

        collection_soup = BeautifulSoup(collection_response.text, "html.parser")
        for paragraph in collection_soup.find("div", class_="editor").find_all("p"):
            matches = re.match(
                r"^Your next (\w+) collections: (.*), (.*)", paragraph.text
            )
            if matches:
                collection_type, first_date_string, second_date_string = (
                    matches.groups()
                )
                try:
                    first_date = datetime.strptime(
                        first_date_string, "%A %d %B %Y"
                    ).date()
                except ValueError:
                    first_date = datetime.strptime(
                        first_date_string, "%A %d %b %Y"
                    ).date()
                try:
                    second_date = datetime.strptime(
                        second_date_string.strip(), "%A %d %B %Y"
                    ).date()
                except ValueError:
                    second_date = datetime.strptime(
                        second_date_string.strip(), "%A %d %b %Y"
                    ).date()

                entries.append(
                    Collection(
                        date=first_date,
                        t=collection_type.capitalize(),
                        icon=ICON_MAP.get(collection_type.capitalize()),
                    )
                )
                if second_date != first_date:
                    entries.append(
                        Collection(
                            date=second_date,
                            t=collection_type.capitalize(),
                            icon=ICON_MAP.get(collection_type.capitalize()),
                        )
                    )
        if not entries:
            raise ValueError(
                "Could not get collections for the given combination of UPRN and Postcode."
            )

        return entries
