import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Horsham District Council"
DESCRIPTION = "Source script for Horsham District Council"
URL = "https://www.horsham.gov.uk"
TEST_CASES = {
    "Blackthorn Avenue - number": {"uprn": 10013792881},
    "Blackthorn Avenue - string": {"uprn": "10013792881"},
}
API_URL = "https://satellite.horsham.gov.uk/environment/refuse/cal_details.asp"
ICON_MAP = {
    "Refuse Bin for Non-Recycling": "mdi:trash-can",
    "Blue-Top Bin for Recycling": "mdi:recycle",
    "Brown-Top Bin for Garden Waste": "mdi:leaf",
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, uprn: str):
        self._uprn = str(uprn)

    def fetch(self):
        entries = []

        r = requests.post(
            API_URL,
            data={"uprn": self._uprn},
        )

        soup = BeautifulSoup(r.text, features="html.parser")
        results = soup.find_all("tr")

        for result in results:
            result_row = result.find_all("td")
            if (
                len(result_row) == 0
            ):  # This removes the first header row, or any rows with no data
                continue
            else:
                date = datetime.strptime(
                    result_row[1].text, "%d/%m/%Y"
                ).date()  # Pull out the rows date

                collection_text = result_row[2].text.replace(
                    "\xa0", " "
                )  # This is to remove a non-blanking space
                collection_items = collection_text.split(
                    "AND"
                )  # Sometimes there will be multiple bins, split with the word AND
                for collection_type in collection_items:
                    entries.append(
                        Collection(
                            date=date,
                            t=collection_type.strip(),  # Strip added to remove trailing white space
                            icon=ICON_MAP.get(
                                collection_type.strip()
                            ),  # Strip added to remove trailing white space
                        )
                    )
        return entries
