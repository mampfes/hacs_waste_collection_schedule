from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "London Borough of Hounslow"
DESCRIPTION = "Source for London Borough of Hounslow."
URL = "https://hounslow.gov.uk"
TEST_CASES = {
    "10090801236": {"uprn": 10090801236},
    "100021552942": {"uprn": 100021552942},
}


ICON_MAP = {
    "Black": "mdi:trash-can",
    "Garden": "mdi:leaf",
    "Recycling": "mdi:recycle",
    "Food": "mdi:food",
}


API_URL = "https://www.hounslow.gov.uk/homepage/86/recycling_and_waste_collection_day_finder#collectionday"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str = str(uprn)

    def fetch(self):
        args = {
            "UPRN": self._uprn,
        }
        r = requests.post(API_URL, data=args)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        bin_cal_divs = soup.find_all("div", class_="bin_day_main_wrapper")
        entries = []

        for bin_cal_div in bin_cal_divs:
            # Extract the address information
            collection_info = bin_cal_div.find_all("h4")
            for info in collection_info:
                date_splitted = info.text.strip().split("-")
                date_str = (
                    date_splitted[1] if len(date_splitted) > 1 else date_splitted[0]
                ).strip()
                try:
                    date = datetime.strptime(date_str, "%d %b %Y").date()
                except ValueError:
                    date = datetime.strptime(date_str, "%A %d %b %Y").date()
                bins = [
                    li.text.strip()
                    for li in info.find_next("ul", class_="list-group").find_all("li")
                ]
                for bin in bins:
                    entries.append(
                        Collection(
                            date=date,
                            t=bin,
                            icon=ICON_MAP.get(bin.split(" ")[0]),
                        )
                    )
        return entries
