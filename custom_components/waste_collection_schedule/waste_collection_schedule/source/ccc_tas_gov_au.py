import datetime
import requests
import json

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


class Source:
    def __init__(self, address: str):
        self.address = address

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update({"content-type": "application/json"})

        address_search_data = {'address': self.address}
        print(json.dumps(address_search_data))
        address_url = "%s/address-search" % URL
        address = session.post(address_url, data=json.dumps(address_search_data))

        if address.status_code != 200:
            raise Exception("Could not find address")
    
        address_result = json.loads(address.content)

        if address_result['success'] == False:
            raise Exception("Could not find address")

        entries = []
        return entries