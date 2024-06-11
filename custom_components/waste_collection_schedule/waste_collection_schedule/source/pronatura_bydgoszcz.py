import datetime
import json
import logging
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Bydgoszcz Garbage Collection"
DESCRIPTION = "Source for Bydgoszcz city garbage collection by Pronatura"
URL = "https://zs5cv4ng75.execute-api.eu-central-1.amazonaws.com/prod"
TEST_CASES = {
    "Street Name": {
        "city": "BYDGOSZCZ",
        "street_name": "LEGNICKA",
        "street_number": 1,
    },
}

_LOGGER = logging.getLogger(__name__)

NAME_MAP_PL = {
    "odpady zmieszane": "Zmieszane odpady komunalne",
    "papier": "Recykling",
    "plastik": "Recykling",
    "szkło": "Recykling",
    "odpady bio": "Bioodpady",
    "odpady wielkogabarytowe": "Odpady wielkogabarytowe",
}

NAME_MAP_EN = {
    "odpady zmieszane": "Trash",
    "papier": "Recycling",
    "plastik": "Recycling",
    "szkło": "Recycling",
    "odpady bio": "Bio",
    "odpady wielkogabarytowe": "Bulk",
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
    def __init__(self, city, street_name, street_number, lang="pl"):
        self._city = city.upper()
        self._street_name = street_name.upper()
        self._street_number = str(street_number).upper()
        self._lang = lang if lang in ["pl", "en"] else "pl"  # Fallback to 'pl' if not 'pl' or 'en'

    def fetch(self):
        try:
            return self.get_data()
        except Exception as e:
            _LOGGER.error(f"fetch failed for source {TITLE}: {e}")
            return []

    def get_data(self):
        streets_url = f"{URL}/streets"
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

        addresses_url = f"{URL}/address-points/{street_id}"
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

        schedule_url = f"{URL}/trash-schedule/{address_id}"
        r = requests.get(schedule_url)
        r.raise_for_status()
        schedule = json.loads(r.text)
        trash_schedule = schedule["trashSchedule"]

        entries = []
        year = schedule["year"]
        name_map = NAME_MAP_EN if self._lang == "en" else NAME_MAP_PL
        for month_schedule in trash_schedule:
            month = self._get_month_number(month_schedule["month"])
            # Collect recykling days
            recykling_days = set()
            for collection in month_schedule["schedule"]:
                waste_type = collection["type"]
                for day in collection["days"]:
                    if waste_type in ["papier", "plastik", "szkło"]:
                        recykling_days.add(int(day))
                    else:
                        entries.append(
                            Collection(
                                datetime.date(year, month, int(day)),
                                name_map[waste_type],
                                ICON_MAP[waste_type],
                            )
                        )
            # Add recykling entries
            for day in recykling_days:
                entries.append(
                    Collection(
                        datetime.date(year, month, day),
                        name_map["papier"],
                        "mdi:recycle",
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
