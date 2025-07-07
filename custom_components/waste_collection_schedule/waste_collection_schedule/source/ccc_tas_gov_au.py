import requests
import json

from datetime import date, timedelta
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Clarence City Council"
COUNTRY = "au"
DESCRIPTION = "The greater Eastern Shore of Hobart"

URL = "https://www.ccc.tas.gov.au/wp-json/waste-collection"
ICON_MAP = {
    "RUBBISH": "mdi:trash-can",
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
    "80 Clarence St": {
        "address": "80 Clarence St"
    },    
    "50 East Derwent Highway": {
        "address": "50 East Derwent Highway"
    },
}

def _get_next_n_dates(date_obj: date, n: int, delta: timedelta):
    next_dates = []
    for _ in range(n):
        while date_obj <= date.today():
            date_obj += delta
        next_dates.append(date_obj)
        date_obj += delta
    return next_dates


def _next_date(value) -> date:
    splits = value.replace(",","").split(" ")
    next_date_raw = splits[-2].split("/")
    return date(int(next_date_raw[2]),int(next_date_raw[1]),int(next_date_raw[0]))
    

def _calculate_frequency(value) -> int:
    splits = value.replace(",","").split(" ")
    
    next_date_raw = splits[-2].split("/")
    next_date_n_raw = splits[-1].split("/")

    next_date = date(int(next_date_raw[2]),int(next_date_raw[1]),int(next_date_raw[0]))
    next_date_n = date(int(next_date_n_raw[2]),int(next_date_n_raw[1]),int(next_date_n_raw[0]))
    frequency = next_date_n - next_date

    return int(frequency.days)


def _process_results(results) -> list[Collection]:
    entries = []

    frequency_rubbish = 0
    next_rubbish = date(1970,1,1)
    frequency_recycling = 0
    next_recycling = date(1970,1,1)
    frequency_greenwaste = 0
    next_greenwaste = date(1970,1,1)

    for result in results:
        if result['name'] == "Waste Collection Day":
            collection_day = result['value']
        
        if result['name'] == 'Garbage Pickup':
            frequency_rubbish = _calculate_frequency(result['value'])
            next_rubbish = _next_date(result['value'])

        if result['name'] == 'Recycling Pickup':
            frequency_recycling = _calculate_frequency(result['value'])
            next_recycling = _next_date(result['value'])

        if result['name'] == 'Green Waste Pickup':
            frequency_greenwaste = _calculate_frequency(result['value'])
            next_greenwaste = _next_date(result['value'])

    rubbish_collection_dates = _get_next_n_dates(
        next_rubbish, 52, timedelta(days=frequency_rubbish)
    )

    recycling_collection_dates = _get_next_n_dates(
        next_recycling, 52, timedelta(days=frequency_recycling)
    )

    greenwaste_collection_dates = _get_next_n_dates(
        next_greenwaste, 52, timedelta(days=frequency_greenwaste)
    )

    entries.extend(
        [
            Collection(date=collection_date, t="Rubbish", icon=ICON_MAP["RUBBISH"])
            for collection_date in rubbish_collection_dates
        ]
    )

    entries.extend(
        [
            Collection(date=collection_date, t="Recycling", icon=ICON_MAP["RECYCLE"])
            for collection_date in recycling_collection_dates
        ]
    )

    entries.extend(
        [
            Collection(date=collection_date, t="Greenwaste", icon=ICON_MAP["ORGANIC"])
            for collection_date in greenwaste_collection_dates
        ]
    )
    
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
            raise Exception("Could not complete addres lookup %i" % address.status_code)
    
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

        return _process_results(collections_result['results'])