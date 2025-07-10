import datetime
import requests
from waste_collection_schedule import Collection

TITLE = "Cyclad"
DESCRIPTION = "Source for cyclad.org waste collection schedules"
URL = "https://cyclad.org/"
COUNTRY = "fr"

TEST_CASES = {
    "Nancras": {"commune_id": 254},
}

ICON_MAP = {
    "Emballage": "mdi:recycle",
    "Ordures ménagères": "mdi:trash-can",
    "emballages ordures": "mdi:trash-can",
}

class Source:
    def __init__(self, commune_id: int):
        self._commune_id = str(commune_id)

    def fetch(self):
        url = "https://cyclad.org/wp/wp-admin/admin-ajax.php"
        response = requests.post(url, data={"action": "ajax_calendar_autocomplete", "post_id": self._commune_id})
        response.raise_for_status()
        data = response.json()
        if not data:
            return []
        dates = data[0].get("dates", {})
        today = datetime.date.today()
        entries = []

        def add(date_str: str, bin_type: str):
            try:
                dt = datetime.datetime.strptime(date_str, "%d/%m/%Y").date()
            except ValueError:
                return
            if dt >= today:
                entries.append(Collection(date=dt, t=bin_type, icon=ICON_MAP.get(bin_type)))

        for bin_type, value in dates.items():
            if bin_type == "intersect":
                for name, arr in value.items():
                    pretty = name.replace("_", " ")
                    for d in arr:
                        add(d, pretty)
            elif isinstance(value, dict):
                for d in value.values():
                    add(d, bin_type)
        entries.sort(key=lambda x: x.date)
        return entries
