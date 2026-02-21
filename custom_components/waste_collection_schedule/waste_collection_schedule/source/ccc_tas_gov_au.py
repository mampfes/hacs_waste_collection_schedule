import re
from datetime import date, datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Clarence City Council"
COUNTRY = "au"
DESCRIPTION = "The greater Eastern Shore of Hobart"

URL = "https://www.ccc.tas.gov.au/wp-json/waste-collection"
ICON_MAP = {
    "RUBBISH": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GREENWASTE": "mdi:leaf",
}

PARAM_DESCRIPTIONS = {"en": {"address": "The address of the collection"}}

PARAM_TRANSLATIONS = {"en": {"address": "123 Clarence St ROSNY TAS 7018"}}

TEST_CASES = {
    "80 Clarence St": {"address": "80 Clarence St"},
    "50 East Derwent Highway": {"address": "50 East Derwent Highway"},
}

DATE_REGEX = r"\d{1,2}/\d{1,2}/\d{4}"
WEEKS_TO_CHECK = 52


def _get_dates(value: str) -> list[date]:
    date_strings = re.findall(DATE_REGEX, value)
    dates = []

    # If we have anything other than two dates
    # then API has changed and we should not process the data
    if len(date_strings) == 2:
        next_pickup = datetime.strptime(date_strings[0], "%d/%m/%Y")
        next_pickup_plus_one = datetime.strptime(date_strings[1], "%d/%m/%Y")
        dates.append(next_pickup.date())
        dates.append(next_pickup_plus_one.date())
        date_delta = next_pickup_plus_one - next_pickup

        for _ in range(WEEKS_TO_CHECK):
            next_pickup_plus_one += date_delta
            dates.append(next_pickup_plus_one.date())
    else:
        raise Exception("Data has changed, api processor needs to be updated")

    return dates


def _process_results(results) -> list[Collection]:
    entries = []

    collections: dict[str, list[date]] = {}

    # Results also include hard waste#
    # but council do not do hardwaste pickups anymore so omitted intentionally
    for result in results:
        if result["name"] == "Garbage Pickup":
            collections["Rubbish"] = _get_dates(result["value"])

        if result["name"] == "Recycling Pickup":
            collections["Recycling"] = _get_dates(result["value"])

        if result["name"] == "Green Waste Pickup":
            collections["Greenwaste"] = _get_dates(result["value"])

    for bin_type, dates in collections.items():
        entries.extend(
            [
                Collection(
                    date=collection_date, t=bin_type, icon=ICON_MAP[bin_type.upper()]
                )
                for collection_date in dates
            ]
        )
    return entries


def _query_api(address: str) -> dict:
    session = requests.Session()
    session.headers.update({"content-type": "application/json"})

    address_search_data = {"address": address}
    address_url = "%s/address-search" % URL
    address_result = session.post(address_url, json=address_search_data)

    if address_result.status_code != 200:
        raise Exception(
            "Could not complete address lookup %i" % address_result.status_code
        )

    address_data = address_result.json()

    if not address_data["success"]:
        raise Exception("Could not find address")

    ccc_formatted_address = address_data["results"][0]

    collection_search_data = {"address": ccc_formatted_address}
    collection_url = "%s/collection-search" % URL
    collections = session.post(collection_url, json=collection_search_data)

    if address_result.status_code != 200:
        raise Exception("Could not find collections")

    collections_result = collections.json()

    if not collections_result["success"]:
        raise Exception("Could not find collections")

    return collections_result


class Source:
    def __init__(self, address: str):
        self.address = address

    def fetch(self) -> list[Collection]:
        collections_result = _query_api(self.address)

        return _process_results(collections_result["results"])
