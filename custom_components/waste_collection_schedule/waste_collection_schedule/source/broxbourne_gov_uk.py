import datetime
import logging

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Borough of Broxbourne Council"
DESCRIPTION = "Source for broxbourne.gov.uk services for Broxbourne, UK."
URL = "https://www.broxbourne.gov.uk"
TEST_CASES = {
    "Old School Cottage (Domestic Waste Only)": {
        "uprn": "148040092",
        "postcode": "EN10 7PX",
    },
    "11 Park Road (All Services)": {"uprn": "148028240", "postcode": "EN11 8PU"},
    "11 Pulham Avenue (All Services)": {"uprn": 148024643, "postcode": "EN10 7TA"},
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

        # The council API returns no year for the collections
        # and so it needs to be calculated to format the date correctly

        today = datetime.date.today()
        year = today.year

        for item in tr[1:]:  # Ignore table header row
            td = item.findAll("td")
            waste_type = td[1].text.rstrip()

            # We need to replace characters due to encoding in form
            collection_date_text = (
                td[0].text.split(" ")[0].replace("\xa0", " ") + " " + str(year)
            )

            try:
                # Broxbourne give an empty date field where there is no collection
                collection_date = datetime.datetime.strptime(
                    collection_date_text, "%a %d %B %Y"
                ).date()

            except ValueError as e:
                LOGGER.warning(
                    f"No date found for wastetype: {waste_type}. The date field in the table is empty or corrupted. Failed with error: {e}"
                )
                continue

            # Calculate the year. As we only get collections a week in advance we can assume the current
            # year unless the month is January in December where it will be next year

            if (collection_date.month == 1) and (today.month == 12):
                collection_date = collection_date.replace(year=year + 1)

            entries.append(
                Collection(
                    date=collection_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries
