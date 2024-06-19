import datetime
import json
import logging
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Bydgoszcz Pronatura"
DESCRIPTION = "Source for Bydgoszcz city garbage collection by Pronatura"
URL = "http://www.pronatura.bydgoszcz.pl/"
API_URL = "https://zs5cv4ng75.execute-api.eu-central-1.amazonaws.com/prod"
COUNTRY = "pl"
TEST_CASES = {
    "Case1": {
        "street_name": "LEGNICKA",
        "street_number": 1,
    },
    "Case2": {
        "street_name": "JÓZEFA SOWIŃSKIEGO",
        "street_number": "22A",
    },
}

_LOGGER = logging.getLogger(__name__)

NAME_MAP = {
    "odpady zmieszane": "Zmieszane odpady komunalne",
    "papier": "Papier",
    "plastik": "Metale i tworzywa sztuczne",
    "szkło": "Szkło",
    "odpady bio": "Bioodpady",
    "odpady wielkogabarytowe": "Odpady wielkogabarytowe",
}

ICON_MAP = {
    "odpady zmieszane": "mdi:trash-can",
    "papier": "mdi:recycle",
    "plastik": "mdi:recycle",
    "szkło": "mdi:recycle",
    "odpady bio": "mdi:leaf",
    "odpady wielkogabarytowe": "mdi:wardrobe",
}

class Source:
    def __init__(self, street_name, street_number):
        self._street_name = street_name.upper()
        self._street_number = str(street_number).upper()

    def fetch(self):
        return self.get_data()

    def get_data(self):
        streets_url = f"{API_URL}/streets"
        r = requests.get(streets_url)
        r.raise_for_status()
        streets = json.loads(r.text)
        street_id = None
        for street in streets:
            if street["street"].upper() == self._street_name:
                street_id = street["id"]
                break
        if street_id is None:
            raise Exception("Street not found")

        addresses_url = f"{API_URL}/address-points/{street_id}"
        r = requests.get(addresses_url)
        r.raise_for_status()
        addresses = json.loads(r.text)
        address_id = None
        for address in addresses:
            if address["buildingNumber"].upper() == self._street_number:
                address_id = address["id"]
                break
        if address_id is None:
            raise Exception("Address not found")

        schedule_url = f"{API_URL}/trash-schedule/{address_id}"
        r = requests.get(schedule_url)
        r.raise_for_status()
        schedule = json.loads(r.text)
        trash_schedule = schedule["trashSchedule"]

        entries = []
        year = schedule["year"]
        for month_schedule in trash_schedule:
            month = self._get_month_number(month_schedule["month"])
            for collection in month_schedule["schedule"]:
                waste_type = collection["type"]
                for day in collection["days"]:
                    entries.append(
                        Collection(
                            datetime.date(year, month, int(day)),
                            NAME_MAP[waste_type],
                            ICON_MAP[waste_type],
                        )
                    )
        return entries

    def _get_month_number(self, month_name):
        month_map = {
            "Styczeń": 1,
            "Luty": 2,
            "Marzec": 3,
            "Kwiecień": 4,
            "Maj": 5,
            "Czerwiec": 6,
            "Lipiec": 7,
            "Sierpień": 8,
            "Wrzesień": 9,
            "Październik": 10,
            "Listopad": 11,
            "Grudzień": 12,
        }
        return month_map[month_name]
