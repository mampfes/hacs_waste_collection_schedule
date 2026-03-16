import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Silea"
DESCRIPTION = "Silea"
URL = "https://www.sileaspa.it"

API = "https://www.sileaspa.it/wp-admin/admin-ajax.php"
TEST_CASES = {
    "Test_001": {"municipality": "Lomagna", "address": "via martiri"},
    "Test_002": {"municipality": "Cesana", "address": "via foscolo"},
}
ICON_MAP = {
    "INDIFFERENZIATO": "mdi:trash-can",
    "PLASTICA, LATTINE E TETRAPAK": "mdi:recycle",
    "VETRO": "mdi:bottle-wine",
    "CARTA E CARTONE": "mdi:newspaper-variant-multiple",
    "SPAZZAMENTO MECCANIZZATO": "mdi:tanker-truck",
    "UMIDO": "mdi:leaf",
}

class Source:
    def __init__(self, municipality, address):
        self._municipality = None
        self._address = None

        s = requests.Session()

        # Retrieve Municipality/town
        payload = {"action": "get_comuni"}
        resp = s.post(API, data=payload)
        data = json.loads(resp.text)

        for item in data:
            if municipality.lower() in item["name"].lower():
                self._municipality = item["id"]
                break

        # Raise error if municipality is not found
        if self._municipality is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality",
                self._municipality,
                [item["name"].title() for item in data],
            )

        # Retrieve Street
        payload = {"action": "get_vie", "id_cliente": self._municipality}
        resp = s.post(API, data=payload)
        data = json.loads(resp.text)

        for item in data:
            if address.lower() in item["name"].lower():
                self._address = item["id"]
                break

        # Raise error if address is not found
        if self._address is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "address", self._address, [item["name"].title() for item in data]
            )

    def fetch(self):
        entries = []
        s = requests.Session()

        payload = {
            "action": "get_months",
            "id_cliente": self._municipality,
            "id_via": self._address,
        }
        resp = s.post(API, data=payload)
        available_months = resp.json()

        for month in available_months:
            payload = {
                "action": "get_calendar",
                "id_cliente": self._municipality,
                "id_via": self._address,
                "id_mese": month["id"],
            }
            resp = s.post(API, data=payload)
            month_data = resp.json()
            
            for item in month_data:
                try:
                    # use 'format' field, already in YYYY-MM-DD format
                    date_str = item.get("format")
                    if not date_str:
                        continue
                    collection_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except Exception:
                    continue
                
                for service in item.get("services", []):
                    # Service name is something like "INDIFFERENZIATO" or "CARTA E CARTONE"
                    raw_name = service.get("service", "").strip()
                
                    entries.append(
                        Collection(
                            date=collection_date,
                            t=raw_name.title(),
                            icon=ICON_MAP.get(raw_name)
                        )
                    )



        return entries
