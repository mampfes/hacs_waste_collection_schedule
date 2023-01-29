import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Maldon District Council"

DESCRIPTION = ("Source for www.maldon.gov.uk services for Maldon, UK")

URL = "https://www.maldon.gov.uk/"

TEST_CASES = {
    "test 1": {"uprn": "200000917928"},
    "test 2": {"uprn": "100091258454"},
}

API_URL = "https://maldon.suez.co.uk/maldon/ServiceSummary?uprn="

ICON_MAP = {
    "Refuse Collection": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Green": "mdi:leaf",
    "Food": "mdi:food-apple",
}

class Source:
    def __init__(self, uprn: str):
        self._uprn = uprn

    def _extract_future_date(self, text):
        # parse both dates and return the future one
        dates = re.findall(r'\d{2}/\d{2}/\d{4}', text)
        dates = [datetime.strptime(date, '%d/%m/%Y').date() for date in dates]
        return max(dates)

    def fetch(self):
        entries = []

        session = requests.Session()

        r = session.get(f"{API_URL}{self._uprn}")
        soup = BeautifulSoup(r.text, features="html.parser")
        collections = soup.find_all("div", {"class": "panel-default"})

        if not collections:
            raise Exception("No collections found for given UPRN")

        for collection in collections:
            # check is a collection row
            title = collection.find("h2", {"class": "panel-title"}).text.strip()

            if title == "Other Services" or "You are not currently subscribed" in collection.text:
                continue

            entries.append(
                Collection(
                    date=self._extract_future_date(collection.text),
                    t=title,
                    icon=ICON_MAP.get(title),
                )
            )

        return entries
