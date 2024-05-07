import re
from datetime import datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Birmingham City Council"
DESCRIPTION = "Source for birmingham.gov.uk services for Birmingham, UK."
URL = "https://birmingham.gov.uk"
TEST_CASES = {
    "Cherry Tree Croft": {"uprn": "100070321799", "postcode": "B27 6TF"},
    "Ludgate Loft Apartments": {"uprn": "10033389698", "postcode": "B3 1DW"},
    "Windermere Road": {"uprn": "100070566109", "postcode": "B13 9JP"},
    "Park Hill": {"uprn": "100070475114", "postcode": "B13 8DS"},
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36",
}

API_URLS = {
    "get_session": "https://www.birmingham.gov.uk/xfp/form/619",
    "collection": "https://www.birmingham.gov.uk/xfp/form/619",
}
ICON_MAP = {
    "Household Collection": "mdi:trash-can",
    "Recycling Collection": "mdi:recycle",
    "Green Recycling Chargeable Collections": "mdi:leaf",
}


class Source:
    def __init__(self, uprn: str, postcode: str):
        self._uprn = uprn
        self._postcode = postcode

    def fetch(self):
        entries: list[Collection] = []

        session = requests.Session()
        session.headers.update(HEADERS)

        token_response = session.get(API_URLS["get_session"])
        soup = BeautifulSoup(token_response.text, "html.parser")
        token = soup.find("input", {"name": "__token"}).attrs["value"]
        if not token:
            raise ValueError(
                "Could not parse CSRF Token from initial response. Won't be able to proceed."
            )

        form_data = {
            "__token": token,
            "page": "491",
            "locale": "en_GB",
            "q1f8ccce1d1e2f58649b4069712be6879a839233f_0_0": self._postcode,
            "q1f8ccce1d1e2f58649b4069712be6879a839233f_1_0": self._uprn,
            "next": "Next",
        }

        collection_response = session.post(API_URLS["collection"], data=form_data)

        collection_soup = BeautifulSoup(collection_response.text, "html.parser")

        for table_row in collection_soup.find("table", class_="data-table").tbody.find_all("tr"):
            collection_type = table_row.contents[0].text

            if collection_type not in ICON_MAP:
                continue

            collection_next = table_row.contents[1].text
            collection_date = re.findall("\(.*?\)", collection_next)

            if len(collection_date) != 1:
                continue

            collection_date_obj = parse(re.sub("[()]", "", collection_date[0])).date()

            # since we only have the next collection day, if the parsed date is in the past,
            # assume the day is instead next month
            if collection_date_obj < datetime.now().date():
                collection_date_obj += relativedelta(months=1)

            entries.append(
                Collection(
                    date=collection_date_obj,
                    t=collection_type,
                    icon=ICON_MAP.get(collection_type),
                )
            )

        if not entries:
            raise ValueError(
                "Could not get collections for the given combination of UPRN and Postcode."
            )

        return entries
