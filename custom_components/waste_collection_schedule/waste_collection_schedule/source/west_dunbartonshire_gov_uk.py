import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "West Dunbartonshire Council"
DESCRIPTION = "Source for waste collection services from West Dunbartonshire Council"
URL = "https://www.west-dunbarton.gov.uk"
TEST_CASES = {
    "2/2 26 Kilbowie Road, Clydebank": {"uprn": "129040292"},
    "6A Victoria Street, Dumbarton": {"uprn": "129033978"},
    "8 Clairinsh, Balloch": {"uprn": "129491488"},
    "Rowan Lea, Gartocharn": {"uprn": "129490987"},
    "20 35 Risk Street, Dumbarton": {"uprn": "129003614"},
}

API_URL = "https://www.west-dunbarton.gov.uk/recycling-and-waste/bin-collection-day"
ICON_MAP = {
    "BLACK": "mdi:trash-can",
    "BLUE": "mdi:recycle",
    "BROWN": "mdi:leaf",
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}


_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):

        s = requests.Session()

        if self._uprn:
            # GET request returns page containing links to separate collection schedules
            params = {"uprn": self._uprn}
            r = s.get(API_URL, params=params, headers=HEADERS)
            r.raise_for_status()
            responseContent = r.text
            soup = BeautifulSoup(responseContent, "html.parser")

            # For each next-date class get the text within the date-string class
            schedule_details = soup.findAll("div", {"class": "round-info"})

            # Extract links to collection schedule pages and iterate through the pages
            entries = []
            for item in schedule_details:
                schedule_date = item.find("span", {"class": "date-string"}).text.strip()
                schedule_type = item.find("div", {"class": "round-name"}).text.strip()
                # Format is 22 March 2023 - convert to date
                collection_date = datetime.strptime(schedule_date, "%d %B %Y").date()

                # If the type contains "Blue bin or bag" or "Blue" then set the type to "BLUE"
                if "bag" in schedule_type.lower() or "blue" in schedule_type.lower():
                    entries.append(
                        Collection(
                            date=collection_date,
                            t="BLUE",
                            icon=ICON_MAP.get("BLUE"),
                        )
                    )

                # If the type contains "caddy" or "brown" then set the type to "BROWN"
                if "caddy" in schedule_type.lower() or "brown" in schedule_type.lower():
                    entries.append(
                        Collection(
                            date=collection_date,
                            t="BROWN",
                            icon=ICON_MAP.get("BROWN"),
                        )
                    )

                # If the type contains "Non-Recyclable" then set the type to "BLACK", compare in lowecase
                if "non-recyclable" in schedule_type.lower():
                    entries.append(
                        Collection(
                            date=collection_date,
                            t="BLACK",
                            icon=ICON_MAP.get("BLACK"),
                        )
                    )

            return entries
