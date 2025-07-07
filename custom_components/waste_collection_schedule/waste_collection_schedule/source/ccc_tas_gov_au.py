import requests
import json

from datetime import date, timedelta
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Clarence City Council"
COUNTRY = "au"
DESCRIPTION = "The greater Eastern Shore of Hobart"

URL = "https://www.ccc.tas.gov.au/wp-json/waste-collection"
ICON_MAP = {
    "DOMESTIC": "mdi:trash-can",
    "RECYCLE": "mdi:recycle",
    "ORGANIC": "mdi:leaf",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "The address of the collection"
    }
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "123 Clarence St ROSNY TAS 7018"
    }
}

TEST_CASES = {
    "71 Clarence St": {
        "address": "71 Clarence St"
    },
}

WEEKDAY_MAP = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


def _get_next_n_dates(date_obj: date, n: int, delta: timedelta):
    next_dates = []
    for _ in range(n):
        date_obj += delta
        while date_obj <= date.today():
            date_obj += delta
        next_dates.append(date_obj)
    return next_dates


def _get_previous_date_for_day_of_week(day_of_week: int):
    today = date.today()
    return today - timedelta((today.weekday() - day_of_week + 7) % 7)

def calculate_frequency(value) -> int:
    splits = value.replace(",","").split(" ")
    print(splits)
    return 0

def process_results(results) -> list[Collection]:
    entries = []

    collection_day = "unknown"
    frequency_rubbish = 0
    frequency_recycling = 0
    frequency_greenwaste = 0

    for result in results:
        if result['name'] == "Waste Collection Day":
            collection_day = result['value']
        
        if result['name'] == 'Garbage Pickup':
            frequency_rubbish = calculate_frequency(result['value'])

        if result['name'] == 'Recycling Pickup':
            print(result['value'])

        if result['name'] == 'Green Waste Pickup':
            print(result['value'])

    return entries


class Source:
    def __init__(self, address: str):
        self.address = address

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update({"content-type": "application/json"})

        address_search_data = {'address': self.address}
        address_url = "%s/address-search" % URL
        address = session.post(address_url, data=json.dumps(address_search_data))

        if address.status_code != 200:
            raise Exception("Could not find address")
    
        address_result = json.loads(address.content)

        if not address_result['success']:
            raise Exception("Could not find address")

        ccc_formatted_address = address_result['results'][0]

        collection_search_data = {'address': ccc_formatted_address}
        collection_url = "%s/collection-search" % URL
        collections = session.post(collection_url, data=json.dumps(collection_search_data))

        if address.status_code != 200:
            raise Exception("Could not find collections")

        collections_result = json.loads(collections.content)

        if not collections_result['success']:
            raise Exception("Could not find collections")

        return process_results(collections_result['results'])