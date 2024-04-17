import datetime

import requests
from waste_collection_schedule import Collection

TITLE = "Gmina Miękinia"
DESCRIPTION = "Source for Gmina Miękinia, Poland"
URL = "https://api.skycms.com.pl"
TEST_CASES = {
    "Brzezina": {"location_id": 8},
}

ICON_MAP = {
    "Zmieszane": "mdi:trash-can",  # Mixed
    "Tworzywa sztuczne": "mdi:recycle",  # Plastic
    "Bioodpady": "mdi:leaf",  # Organic
    "Papier": "mdi:file-outline",  # Paper
    "Szkło": "mdi:glass-fragile",  # Glass
    "Wielkogabaryty": "mdi:sofa-single"
}

API_URL = "https://api.skycms.com.pl/api/v1/rest/garbage/disposals/"


class Source:
    def __init__(self, location_id):
        self._location_id = location_id

    def fetch(self):
        api_headers = {
            'x-skycms-key': '5d0123032115904c9d4ff70522405e60',
            'x-skycms-type': 'iOS',
            'x-skycms-device': '04C977DF-F4BB-4541-AEF2-EB2F454CB4D2'
        }
        api_response = requests.get(API_URL + str(self._location_id), headers=api_headers)

        entries = []

        kinds = api_response.json()['data']['garbage_kinds']

        for k in kinds:
            name = k['name']
            for d in k['disposals']:
                entries.append(
                    Collection(
                        date=datetime.datetime.strptime(d['id'], "%Y-%m-%d").date(),
                        t=name.capitalize(),
                        icon=ICON_MAP.get(name)
                    )
                )

        return entries