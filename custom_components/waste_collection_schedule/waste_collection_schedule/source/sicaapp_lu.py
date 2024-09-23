import json
import re
from datetime import datetime
from typing import Literal

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "SICA"
DESCRIPTION = "Source for SICA."
URL = "https://sicaapp.lu/"
TEST_CASES = {
    "Steinfort": {"commune": "Steinfort"},
    "Kopstal": {"commune": "Kopstal"},
}


ICON_MAP = {
    "RESIDUAL": "mdi:trash-can",
    "ORGANIC": "mdi:food-apple",
    "VALORLUX": "mdi:package-variant",
    "PAPER": "mdi:newspaper",
    "GLASS": "mdi:bottle-soda",
    "TREES": "mdi:tree",
    "CLOTHING": "mdi:tshirt-crew",
}


API_URL = "https://sicaapp.lu/commune/"
# obj = JSON.parse("
JSON_REGEX = re.compile(r'obj = JSON.parse\("(?P<json>.*)"\);')

COMMUNES = [
    "Bertrange",
    "Garnich",
    "Kehlen",
    "Koerich",
    "Kopstal",
    "Mamer",
    "Steinfort",
    "Habscht",
]
COMMUNES_LITERAL = Literal[
    "Bertrange",
    "Garnich",
    "Kehlen",
    "Koerich",
    "Kopstal",
    "Mamer",
    "Steinfort",
    "Habscht",
]


class Source:
    def __init__(self, commune: COMMUNES_LITERAL):
        self._commune: str = commune

    def fetch(self) -> list[Collection]:
        args = {"commune": self._commune, "submitcommune": "save", "language": ""}

        r = requests.get(API_URL, params=args)
        r.raise_for_status()

        m = JSON_REGEX.search(r.text)
        if m is None:
            raise ValueError("No JSON data found")
        data_str = m.group("json").encode().decode("unicode_escape")
        data = json.loads(data_str)
        if "code" in data and data["code"] == "rest_no_route":
            raise ValueError(f"Commune {self._commune} not, use one of {COMMUNES}")

        entries = []
        for month in data:
            for day in month["schedule"]:
                if not day["pickupTypes"]:
                    continue
                date = datetime.strptime(day["date"], "%Y%m%d").date()
                for waste_type_dict in day["pickupTypes"]:
                    waste_type = waste_type_dict["name"]
                    icon = ICON_MAP.get(re.split(r"\s|,", waste_type)[0])
                    entries.append(Collection(date=date, t=waste_type, icon=icon))

        return entries
