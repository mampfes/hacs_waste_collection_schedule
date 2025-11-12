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
        response.raise_for_status()

        html = BeautifulSoup(response.text, "html.parser")

        table = html.find("table", attrs={"id": "icmsTable-abfallsammlung"})
        if not table:
            return []

        try:
            data = json.loads(table.attrs["data-entities"])
        except (json.JSONDecodeError, KeyError):
            return []

        entries = []
        for item in data.get("data", []):
            try:
                date_html = item["_anlassDate"]
                date_soup = BeautifulSoup(date_html, "html.parser")
                date_text = date_soup.get_text().strip()

                date_str = date_text.split(",")[0].split("-")[0].strip()

                next_pickup_date = datetime.strptime(date_str, "%d.%m.%Y").date()

                waste_type = BeautifulSoup(item["name"], "html.parser").text.strip()

                icon = ICON_MAP.get(waste_type, "mdi:trash-can")

                entries.append(
                    Collection(
                        date=next_pickup_date,
                        t=waste_type,
                        icon=icon,
                    )
                )
            except Exception:
                pass

        return entries
