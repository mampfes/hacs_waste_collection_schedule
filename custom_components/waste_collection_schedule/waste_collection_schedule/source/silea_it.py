import json
import requests

from datetime import datetime
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

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
    "Raccolta carta": "mdi:newspaper-variant-multiple",
    "Spazzamento meccanizzato": "mdi:tanker-truck",
    "Raccolta umido": "mdi:leaf"
}

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
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality", self._municipality, [item["name"].title() for item in data]
            )            

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
            raise SourceArgumentNotFoundWithSuggestions(
                "address", self._address, [item["name"].title() for item in data]
            )
 

    def fetch(self):

        entries = []
        s = requests.Session()

        payload = { "action": "get_months", "id_cliente": self._municipality, "id_via": self._address }
        resp = s.post(API, data=payload)
        available_months = json.loads(resp.text)

        for month in available_months.values():               
            # Get data for each available month
            payload = { "action": "get_calendar", "id_cliente": self._municipality, "id_via": self._address, "id_mese": month['id'] }
            resp = s.post(API, data=payload)
            month_data = json.loads(resp.text)

            # request and process calendar items for each available month
            for item in month_data.values():
                collection_date = datetime.strptime(item['date'], "%Y-%m-%dT%H:%M:%S").date()
                for service in item['services']:
                    service_clean_name = service['service'].replace("  ", " ")
                    entries.append(Collection(date = collection_date, t = service_clean_name, icon = ICON_MAP.get(service_clean_name)))


        return entries

