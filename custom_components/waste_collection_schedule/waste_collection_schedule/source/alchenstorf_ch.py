import json
import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Alchenstorf"
DESCRIPTION = " Source for 'Alchenstorf, CH'"
URL = "https://www.alchenstorf.ch"
TEST_CASES: dict[str, dict] = {"TEST": {}}

ICON_MAP = {
    "Grünabfuhr Alchenstorf": "mdi:leaf",
    "Kehrichtabfuhr Alchenstorf": "mdi:trash-can-outline",
    "Kartonsammlung Alchenstorf": "mdi:recycle",
    "Papiersammlung Alchenstorf": "mdi:newspaper-variant-multiple-outline",
    "Alteisenabfuhr Alchenstorf": "mdi:desktop-classic",
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self):
        pass

    def fetch(self):
        response = requests.get("https://www.alchenstorf.ch/abfalldaten")

        html = BeautifulSoup(response.text, "html.parser")

        table = html.find("table", attrs={"id": "icmsTable-abfallsammlung"})
        data = json.loads(table.attrs["data-entities"])

        entries = []
        for item in data["data"]:
            next_pickup = item["_anlassDate-sort"].split()[0]
            next_pickup_date = datetime.fromisoformat(next_pickup).date()

            waste_type = BeautifulSoup(item["name"], "html.parser").text
            waste_type_sorted = BeautifulSoup(item["name-sort"], "html.parser").text

            entries.append(
                Collection(
                    date=next_pickup_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type_sorted, "mdi:trash-can"),
                )
            )

        return entries
