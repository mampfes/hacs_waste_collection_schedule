import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Nottingham City Council"
DESCRIPTION = (
    "Source for nottinghamcity.gov.uk services for the city of Nottingham, UK."
)
URL = "https://nottinghamcity.gov.uk"
TEST_CASES = {
    "Douglas Rd, Nottingham NG7 1NW": {"uprn": "100031540175"},
    "Harlaxton Drive, Nottingham, NG7 1JE": {"uprn": "100031553830"},
}

BINS = {
    "Recycling": {"icon": "mdi:recycle", "name": "Recycling"},
    "Waste": {"icon": "mdi:trash-can", "name": "General"},
    "Garden": {"icon": "mdi:leaf", "name": "Garden"},
    "Food23L": {"icon": "mdi:food-apple", "name": "Food"},
    "Food23L_bags": {"icon": "mdi:food-apple", "name": "Food"},
}


class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self):
        # get json file
        r = requests.get(
            f"https://geoserver.nottinghamcity.gov.uk/bincollections2/api/collection/{self._uprn}"
        )

        # extract data from json
        data = r.json()

        entries = []

        next_collections = data["nextCollections"]

        # Sometimes the Nottingham City Council API returns multiple collections
        # for the same bin type, with different dates.
        # (e.g. Recycling next Tuesday and Recycling in 400 years time)
        # We want to keep the closest date only for each bin type.

        revised_next_collections = {}  # type: dict[str, datetime.datetime]

        for collection in next_collections:
            bin_type = collection["collectionType"]
            next_collection_date = datetime.datetime.fromisoformat(
                collection["collectionDate"]
            )

            if bin_type in revised_next_collections:
                revised_next_collections[bin_type] = min(
                    next_collection_date, revised_next_collections[bin_type]
                )
            else:
                revised_next_collections[bin_type] = next_collection_date

        for bin_type, next_collection_date in revised_next_collections.items():
            props = BINS[bin_type]

            entries.append(
                Collection(
                    date=next_collection_date.date(),
                    t=props["name"],
                    icon=props["icon"],
                )
            )

        return entries
