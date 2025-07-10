import requests
from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Cyclad"
DESCRIPTION = "Source for cyclad.org waste collection schedules"
URL = "https://cyclad.org/"
COUNTRY = "fr"

TEST_CASES = {
    "Nancras": {"city_id": 254},
}

ICON_MAP = {
    "Emballage": "mdi:recycle",
    "Ordures ménagères": "mdi:trash-can",
    "biodechets": "mdi:leaf",
}

API_URL = "https://cyclad.org/wp/wp-admin/admin-ajax.php"

class Source:
    def __init__(self, city_id: int):
        self._city_id = city_id

    def fetch(self):
        response = requests.post(
            API_URL,
            data={"action": "ajax_calendar_autocomplete", "post_id": self._city_id},
        )
        response.raise_for_status()
        data = response.json()
        if not data:
            return []
        schedules = data[0].get("dates", {})
        entries = []
        for waste_type, dates in schedules.items():
            if not dates:
                continue
            if isinstance(dates, dict):
                date_list = dates.values()
            elif isinstance(dates, list):
                date_list = dates
            else:
                continue
            for date_str in date_list:
                try:
                    dt = datetime.strptime(date_str, "%d/%m/%Y").date()
                except ValueError:
                    continue
                entries.append(
                    Collection(
                        date=dt,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )
        return entries
