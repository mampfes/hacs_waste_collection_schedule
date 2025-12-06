import logging
import requests
from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Stadtwerke Rösrath"
DESCRIPTION = " Source for 'Stadtwerke Rösrath'."
URL = "https://www.stadtwerke-roesrath.de/service/abfuhrkalender/"
TEST_CASES = {"Ahornweg": {"street": "Ahornweg"}}

_LOGGER = logging.getLogger(__name__)

ICON_MAP = {
    "Biotonne": "mdi:leaf",
    "Restmülltonne": "mdi:trash-can",
    "Restmülltonne 60l": "mdi:trash-can",
    "Gelbe Tonne": "mdi:recycle",
    "Papiertonne": "mdi:package-variant",
}


class Source:
    def __init__(self, street):
        self.street = street

    def fetch(self):
        form = {
            "street": self.street,
        }
        header = {
            "referer": "https://www.stadtwerke-roesrath.de/service/abfuhrkalender/"}
        r = requests.post(
            "https://www.stadtwerke-roesrath.de/wp-admin/admin-ajax.php?action=binalarm_filter",
            data=form,
            headers=header,
        )
        r.raise_for_status()

        data = r.json()

        if len(data) == 0:
            raise Exception("no address found")

        entries = []
        for item in data:
            date = datetime.strptime(item["start"], "%Y-%m-%d").date()
            typ = item["title"]
            icon = ICON_MAP.get(typ)
            entries.append(Collection(date, typ, icon))

        return entries
