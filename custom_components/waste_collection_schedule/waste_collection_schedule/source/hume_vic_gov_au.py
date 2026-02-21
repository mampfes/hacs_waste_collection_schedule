import json
import re
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Hume City Council"
DESCRIPTION = "Source for hume.vic.gov.au Waste Collection Services"
URL = "https://hume.vic.gov.au"
TEST_CASES = {
    "19 Potter": {
        "address": "19 Potter Street Craigieburn 3064",
        "predict": True,
    },
    "1/90 Vineyard": {"address": "1/90 Vineyard Road Sunbury, VIC 3429"},  # Wednesday
    "9-19 McEwen": {"address": "9-19 MCEWEN DRIVE SUNBURY VICTORIA 3429"},  # Wednesday
    "33 Toyon": {"address": "33 TOYON ROAD KALKALLO  3064"},  # Friday
}

API_URLS = {
    "address_search": "https://www.hume.vic.gov.au/api/v1/myarea/search",
    "collection": "https://www.hume.vic.gov.au/ocapi/Public/myarea/wasteservices",
}

HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
    "accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://www.hume.vic.gov.au/Residents/Waste/Know-my-bin-day",
    "Sec-Fetch-Site": "same-origin",
    "X-Requested-With": "XMLHttpRequest",
}

ICON_MAP = {
    "Garbage": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Food and garden": "mdi:leaf",
}


class Source:
    def __init__(self, address="", predict=False):
        address = address.strip()
        address = re.sub(" +", " ", address)
        address = re.sub(",", "", address)
        address = re.sub(r"victoria (\d{4})", " \\1", address, flags=re.IGNORECASE)
        address = re.sub(r" vic (\d{4})", " \\1", address, flags=re.IGNORECASE)
        self.address = address

        if not isinstance(predict, bool):
            raise Exception("'predict' must be a boolean value")
        self.predict = predict

    def collect_dates(self, start_date, weeks):
        dates = []
        dates.append(start_date)
        for i in range(1, int(4 / weeks)):
            start_date = start_date + timedelta(days=(weeks * 7))
            dates.append(start_date)
        return dates

    def fetch(self):
        locationId = 0
        # Retrieve suburbs
        r = requests.get(
            API_URLS["address_search"],
            params={"keywords": self.address},
            headers=HEADERS,
        )

        data = json.loads(r.text)

        # Find the ID for our suburb
        for item in data["Items"]:
            locationId = item["Id"]
            break

        if locationId == 0:
            raise Exception(f"Could not find address: {self.address}")

        # Retrieve the upcoming collections for our property
        r = requests.get(
            API_URLS["collection"],
            params={"geolocationid": locationId, "ocsvclang": "en-AU"},
            headers=HEADERS,
        )

        data = json.loads(r.text)

        responseContent = data["responseContent"]

        soup = BeautifulSoup(responseContent, "html.parser")
        services = soup.find_all("div", attrs={"class": "waste-services-result"})

        entries = []

        for item in services:
            # test if <div> contains a valid date. If not, is is not a collection item.
            date_text = item.find("div", attrs={"class": "next-service"})

            # The date format currently used on https://www.hume.vic.gov.au/Residents/Waste/Know-my-bin-day
            date_format = "%a %d/%m/%Y"

            try:
                # Strip carriage returns and newlines out of the HTML content
                cleaned_date_text = (
                    date_text.text.replace("\r", "").replace("\n", "").strip()
                )

                # Parse the date
                date = datetime.strptime(cleaned_date_text, date_format).date()

            except ValueError:
                continue

            waste_type = item.find("h3").text.strip()

            dates = [date]

            if self.predict:
                interval_text = item.find("div", attrs={"class": "note"})
                if "fortnight" in interval_text.get_text():
                    weeks = 2
                elif "same day each week" in interval_text.get_text():
                    weeks = 1
                dates = self.collect_dates(date, weeks)

            for d in dates:
                entries.append(
                    Collection(
                        date=d,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type, "mdi:trash-can"),
                    )
                )

        return entries
