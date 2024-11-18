import json
import requests
import logging

from datetime import datetime
from waste_collection_schedule import Collection
from collections import defaultdict

TITLE = "Silea"
DESCRIPTION = "Silea"
URL = "https://www.sileaspa.it"

API = "https://www.sileaspa.it/wp-admin/admin-ajax.php"
TEST_CASES = {
    "Test_001": { "municipality": "Lomagna", "address": "via martiri" },
    "Test_002": { "municipality": "Cesana",  "address": "via foscolo" }
}
ICON_MAP = {
    "Raccolta indifferenziato": "mdi:trash-can",
    "Raccolta sacco viola": "mdi:recycle",
    "Raccolta vetro": "mdi:bottle-wine",
    "Raccolta carta": "mdi:newspaper-variant-multiple"
}
ICON_MAP = defaultdict(lambda: "mdi:trash-can", ICON_MAP)

_LOGGER = logging.getLogger(__name__)

class Source:
    def __init__(self, municipality, address):

        self._municipality = None
        self._address = None
        
        s = requests.Session()

        # Retrieve Municipality/town
        payload = { "action": "get_comuni" }
        resp = s.post(API, data=payload)
        data = json.loads(resp.text)

        for item in data:
            if municipality.lower() in item['name'].lower():
                self._municipality = item['id']
                break

        # Raise error if municipality is not found    
        if self._municipality == None:
            raise Exception(f"Cannot find municipality '{municipality}'")
            
        # Retrieve Street
        payload = { "action": "get_vie", "id_cliente": self._municipality }
        resp = s.post(API, data=payload)
        data = json.loads(resp.text)

        for item in data:
            if address.lower() in item['name'].lower():
                self._address = item['id']
                break

        # Raise error if address is not found
        if self._address == None:
            raise Exception(f"Cannot find address '{address}'")
        

    def fetch(self):

        entries = []
        all_months_data = {}

        s = requests.Session()

        payload = { "action": "get_months", "id_cliente": self._municipality, "id_via": self._address }
        resp = s.post(API, data=payload)
        json_months = json.loads(resp.text)
        for key, value in json_months.items():               
            # Get data for each available month
            payload = { "action": "get_calendar", "id_cliente": self._municipality, "id_via": self._address, "id_mese": value['id'] }
            resp = s.post(API, data=payload)
            json_this_month = json.loads(resp.text)
            # merge this month data
            all_months_data = { **all_months_data, **json_this_month }

        # process response        
        for key, value in all_months_data.items():
            collection_date = datetime.strptime(value['date'], "%Y-%m-%dT%H:%M:%S").date()
            for service in value['services']:
                entries.append(Collection(date = collection_date, t = service['service'], icon = ICON_MAP[service['service']]))


        return entries

