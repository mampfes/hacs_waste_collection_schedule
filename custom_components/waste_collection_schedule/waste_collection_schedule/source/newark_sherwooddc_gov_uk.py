import calendar
import datetime
import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Newark & Sherwood District Council"
DESCRIPTION = "Source for Newark & Sherwood services."
URL = "https://www.newark-sherwooddc.gov.uk/"
TEST_CASES = {
    "Edwinstowe": {"uprn": "010091747078"},
    "Ollerton": {"uprn": 100031463343},
    "Clipstone": {"uprn": "010091745473"},
}

BINS = {
    "recycle": {"icon": "mdi:recycle", "name": "Recycling"},
    "refuse": {"icon": "mdi:trash-can", "name": "General"},
    "garden": {"icon": "mdi:leaf", "name": "Garden"},
    "glass": {"icon": "mdi:glass-fragile", "name": "Glass"},
}


class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self):
        # get json file
        r = requests.get(
            "http://app.newark-sherwooddc.gov.uk/bincollection/calendar",
            params={"pid": self._uprn},
        )

        entries = []

        soup = BeautifulSoup(r.content, "html.parser")

        # Collections are arranged by month, with each month as an individual table
        # Split page by months
        months = soup.find_all("table")

        for month in months:
            # Month and year are set in th
            month_data = month.find("th").get_text(strip=True)
            # Regex the month and year then convert month name to number
            month_data_match = re.search(r"(\w*)\s*(\d{4})", month_data)
            extracted_month_name = month_data_match.group(1)
            month_number = list(calendar.month_name).index(extracted_month_name)
            year = month_data_match.group(2)

            # Each collection for the month is an individual table row with a classname beginning bin_
            rows = month.find_all("tr", class_=re.compile("bin_"))
            for collection_day in rows:
                # Get type of bin collection
                collection_type_match = re.search(
                    r"bin_(\w*)", collection_day["class"][0]
                )
                collection_type = collection_type_match.group(1)

                # Get date of collection
                collection_day_match = re.search(
                    r",\s*\w*\s*(\d{1,2})\w{2}",
                    collection_day.find("td").get_text(strip=True),
                )
                collection_day = collection_day_match.group(1)

                entries.append(
                    Collection(
                        date=datetime.date(
                            int(year), int(month_number), int(collection_day)
                        ),  # Collection date
                        t=BINS.get(collection_type, {}).get(
                            "name", collection_type
                        ),  # Collection type
                        icon=BINS.get(collection_type, {}).get(
                            "icon"
                        ),  # Collection icon
                    )
                )

        return entries
