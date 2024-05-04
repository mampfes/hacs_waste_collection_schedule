import logging

import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Borough of Broxbourne Council"
DESCRIPTION = "Source for broxbourne.gov.uk services for Broxbourne, UK."
URL = "https://www.broxbourne.gov.uk"
TEST_CASES = {
    "Old School Cottage (Domestic Waste Only)": {"uprn": "148040092", "postcode": "EN10 7PX"},
    "11 Park Road (All Services)": {"uprn": "148028240", "postcode": "EN11 8PU"},
}

API_URLS = {
    "get_session": "https://www.broxbourne.gov.uk/bin-collection-date",
    "collection": "https://www.broxbourne.gov.uk/xfp/form/205",
}

LOGGER = logging.getLogger(__name__)

ICON_MAP = {
    "Domestic": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Green Waste": "mdi:leaf",
    "Food": "mdi:food-apple",
}


class Source:
    def __init__(self, uprn: str, postcode: str):
        self._uprn = uprn
        self._postcode = postcode

    def fetch(self):
        entries: list[Collection] = []
        session = requests.Session()

        token_response = session.get(API_URLS["get_session"])
        soup = BeautifulSoup(token_response.text, "html.parser")
        token = soup.find("input", {"name": "__token"}).attrs["value"]
        if not token:
            raise ValueError(
                "Could not parse CSRF Token from initial response. Won't be able to proceed."
            )

        form_data = {
            "__token": token,
            "page": "490",
            "locale": "en_GB",
            "qacf7e570cf99fae4cb3a2e14d5a75fd0d6561058_0_0": self._postcode,
            "qacf7e570cf99fae4cb3a2e14d5a75fd0d6561058_1_0": self._uprn,
            "next": "Next",
        }

        collection_response = session.post(API_URLS["collection"], data=form_data)

        collection_soup = BeautifulSoup(collection_response.text, "html.parser")
        tr = collection_soup.findAll("tr")
        for item in tr[1:]:  # Ignore table header row

            td = item.findAll("td")
            waste_type = t=td[1].text

            try:
                # Broxbourne give an empty date field where there is no collection
                collection_date=datetime.strptime(td[0].text
                                                  .split(" ")[0].replace(u'\xa0', u' '), "%a %d %B").date()
            except ValueError as e:
                LOGGER.warning(
                    f"No date found for wastetype: {waste_type}. The date field in the table is empty or corrupted. Failed with error: {e}"
                )
                continue
            entries.append(
                Collection(
                    date=collection_date,
                    t=waste_type,
                    icon=ICON_MAP.get(td[1].text),
                )
            )

        return entries
