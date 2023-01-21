from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Chichester District Council"
DESCRIPTION = "Source for chichester.gov.uk services for Chichester"
URL = "chichester.gov.uk"

TEST_CASES = {
    "Test_001": {"uprn": "010002476348"},
    "Test_002": {"uprn": "100062612654"},
    "Test_003": {"uprn": "100061745708"},
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden Recycling": "mdi:leaf",
}


class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self):
        session = requests.Session()
        # Start a session
        r = session.get("https://www.chichester.gov.uk/checkyourbinday")
        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")

        # Extract form submission url
        form = soup.find("form", attrs={"id": "WASTECOLLECTIONCALENDARV2_FORM"})
        form_url = form["action"]

        # Submit form
        form_data = {
            "WASTECOLLECTIONCALENDARV2_FORMACTION_NEXT": "Submit",
            "WASTECOLLECTIONCALENDARV2_CALENDAR_UPRN": self._uprn,
        }
        r = session.post(form_url, data=form_data)
        r.raise_for_status()

        # Extract collection dates
        soup = BeautifulSoup(r.text, features="html.parser")
        entries = []
        data = soup.find_all("div", attrs={"class": "bin-days"})
        for bin in data:
            if "print-only" in bin["class"]:
                continue

            type = bin.find("span").contents[0].replace("bin", "").strip().title()
            list_items = bin.find_all("li")
            if list_items:
                for item in list_items:
                    date = datetime.strptime(item.text, "%d %B %Y").date()
                    entries.append(
                        Collection(
                            date=date,
                            t=type,
                            icon=ICON_MAP.get(type),
                        )
                    )

        return entries
