import logging
from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Stadtwerke Rösrath"
DESCRIPTION = " Source for 'Stadtwerke Rösrath'."
URL = "https://www.stadtwerke-roesrath.de/service/abfuhrkalender/"
TEST_CASES = {"Ahornweg": {"street": "Ahornweg"}}

_LOGGER = logging.getLogger(__name__)

ICON_MAP = {
    "Biotonne": Icons.BIO_KITCHEN,
    "Restmülltonne": Icons.GENERAL_WASTE,
    "Restmülltonne 60l": Icons.GENERAL_WASTE,
    "Gelbe Tonne": Icons.PLASTIC_PACKAGING,
    "Papiertonne": Icons.PAPER,
}


class Source:
    def __init__(self, street):
        self.street = street

    def fetch(self):
        form = {
            "street": self.street,
        }
        header = {
            "referer": "https://www.stadtwerke-roesrath.de/service/abfuhrkalender/"
        }
        r = requests.post(
            "https://www.stadtwerke-roesrath.de/wp-admin/admin-ajax.php?action=binalarm_filter",
            data=form,
            headers=header,
        )
        r.raise_for_status()

        data = r.json()

        if len(data) == 0:
            raise SourceArgumentNotFound("street", self.street)

        entries = []
        for item in data:
            date = datetime.strptime(item["start"], "%Y-%m-%d").date()
            typ = item["title"]
            icon = ICON_MAP.get(typ)
            entries.append(Collection(date, typ, icon))

        return entries
