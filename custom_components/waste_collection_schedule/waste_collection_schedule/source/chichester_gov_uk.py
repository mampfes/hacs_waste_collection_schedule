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
        form = soup.find("form", attrs={"id": "WASTECOLLECTIONCALENDARV5_FORM"})
        form_url = form["action"]

        # Submit form
        form_data = {
            "WASTECOLLECTIONCALENDARV5_FORMACTION_NEXT": "Submit",
            "WASTECOLLECTIONCALENDARV5_CALENDAR_UPRN": self._uprn,
        }
        r = session.post(form_url, data=form_data)
        r.raise_for_status()

        # Extract collection dates
        soup = BeautifulSoup(r.text, features="html.parser")
        entries = []
        tables = soup.find_all("table", attrs={"class": "bin-collection-dates"})
        # Data is presented in two tables side-by-side
        for table in tables:
            # Each collection is a table row
            data = table.find_all("tr")
            for bin in data:
                cells = bin.find_all("td")
                # Ignore the header row
                if len(cells) == 2:
                    date = datetime.strptime(cells[0].text, "%d %B %Y").date()
                    # Maintain backwards compatibility - it used to be General Waste and now it is General waste
                    type = cells[1].text.title()
                    entries.append(
                        Collection(
                            date=date,
                            t=type,
                            icon=ICON_MAP.get(type),
                        )
                    )

        return entries
