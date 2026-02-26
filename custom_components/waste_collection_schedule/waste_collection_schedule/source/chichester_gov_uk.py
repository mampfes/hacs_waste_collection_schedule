import re
from datetime import datetime

import cloudscraper
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
        session = cloudscraper.create_scraper()
        # Start a session
        r = session.get("https://www.chichester.gov.uk/checkyourbinday")
        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")

        # Extract form submission url
        form = soup.find(
            "form", attrs={"id": re.compile(r"WASTECOLLECTIONCALENDARV\d+_FORM")}
        )
        ID = form["id"].split("_")[0]
        form_url = form["action"]

        # Submit form
        form_data = {
            f"{ID}_FORMACTION_NEXT": "Submit",
            f"{ID}_CALENDAR_UPRN": self._uprn,
        }
        r = session.post(form_url, data=form_data)
        r.raise_for_status()

        # Extract collection dates
        soup = BeautifulSoup(r.text, features="html.parser")
        entries = []
        bin_divs = soup.find_all("div", class_=re.compile(r"binType-"))
        for bin_div in bin_divs:
            # Each collection is a table row
            bin_type = bin_div.text.strip().title()
            date_div = bin_div.find_next_sibling("div")
            if not date_div:
                continue

            # date format "Friday 27 February 2026"
            date = datetime.strptime(date_div.text.strip(), "%A %d %B %Y").date()
            entries.append(
                Collection(
                    date=date,
                    t=bin_type,
                    icon=ICON_MAP.get(bin_type),
                )
            )

        return entries
