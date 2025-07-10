import datetime
import requests
from waste_collection_schedule import Collection

TITLE = "Cyclad"
DESCRIPTION = "Source for Cyclad waste collection dates"
URL = "https://cyclad.org/"
COUNTRY = "fr"

TEST_CASES = {
    "Nancras": {"city_id": 254},
}

API_URL = "https://cyclad.org/wp/wp-admin/admin-ajax.php"
ACTION = "ajax_calendar_autocomplete"

ICON_MAP = {
    "Emballage": "mdi:recycle",
    "Ordures ménagères": "mdi:trash-can",
    "biodechets": "mdi:leaf",
}

class Source:
    def __init__(self, city_id: int):
        self._city_id = city_id

    def fetch(self):
        r = requests.post(API_URL, data={"action": ACTION, "post_id": self._city_id})
        r.raise_for_status()
        data = r.json()[0]

        entries = []
        for waste_type, dates in data["dates"].items():
            if waste_type == "intersect":
                for sub_type, days in dates.items():
                    label = sub_type.replace("_", " ").title()
                    for d in days:
                        dt = datetime.datetime.strptime(d, "%d/%m/%Y").date()
                        entries.append(Collection(dt, label))
                continue

            for d in dates.values():
                dt = datetime.datetime.strptime(d, "%d/%m/%Y").date()
                entries.append(
                    Collection(dt, waste_type, icon=ICON_MAP.get(waste_type))
                )

        return entries
