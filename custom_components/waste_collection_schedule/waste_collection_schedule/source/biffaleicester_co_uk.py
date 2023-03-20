import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Leicester City Council"
DESCRIPTION = "Source for city of Leicester, UK."
URL = "https://www.leicester.gov.uk"
TEST_CASES = {
    "30 Mayflower Rd, Leicester LE5 5QD": {"post_code": "LE5 5QD", "number": "30"},
    "235 Glenfield Rd, Leicester LE3 6DL": {"uprn": "002465020938"},
}

API_URL = "https://biffaleicester.co.uk/wp-admin/admin-ajax.php"

API_ACTIONS = {"address_search": "get_uprn_api", "collection": "get_details_api"}

HEADERS = {
    "user-agent": "Mozilla/5.0",
}

BINS = {
    "DW": {"icon": "mdi:trash-can", "alias": "Refuse"},
    "RY": {"icon": "mdi:recycle", "alias": "Recycling"},
    "GW": {"icon": "mdi:leaf", "alias": "Green Waste"},
}


class Source:
    def __init__(self, uprn=None, post_code=None, number=None):
        self._uprn = uprn
        self._post_code = post_code
        self._number = number

    def fetch(self):
        # Lookup UPRN
        if not self._uprn:
            p = {"action": API_ACTIONS["address_search"], "postcode": self._post_code}
            r = requests.post(API_URL, headers=HEADERS, data=p)
            r.raise_for_status()
            data = r.json()
            addresses = data["anyType"]

            for address in addresses:
                if address["UPRNAddress"].startswith(self._number + " "):
                    self._uprn = address["UPRNID"]

            if not self._uprn:
                raise Exception(
                    f"Could not find address {self._post_code} {self._number}"
                )

        # Get collections
        p = {"action": API_ACTIONS["collection"], "uprn": self._uprn}
        r = requests.post(API_URL, headers=HEADERS, data=p)
        r.raise_for_status()
        collections = r.json()["anyType"]

        entries = []

        for collection in collections:
            type = collection["ServiceMode"]
            props = BINS[type]

            next_date = datetime.datetime.strptime(
                collection["ServiceDueDate"], "%d/%m/%y"
            ).date()

            entries.append(
                Collection(date=next_date, t=props["alias"], icon=props["icon"])
            )

        return entries
