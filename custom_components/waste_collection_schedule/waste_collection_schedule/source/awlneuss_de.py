import datetime
import json

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "AWL Neuss" # Title will show up in README.md and info.md
DESCRIPTION = "Source for Bürgerportal AWL Neuss waste collection." # Describe your source
URL = "https://buergerportal.awl-neuss.de/" # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = { # Insert arguments for test cases to be used by test_sources.py script
    "Neuss, Theodor-Heuss-Platz 13": { "street_code": 8650, "building_number": 13},
    "Neuss, Niederstrasse 42": { "street_code": 6810, "building_number": 42}
}

API_URL = "https://buergerportal.awl-neuss.de/api/v1/calendar"
ICON_MAP = {
    "grau": "mdi:trash-can",
    "pink": "mdi:trash-can",
    "braun": "mdi:leaf",
    "blau": "mdi:package-variant",
    "gelb": "mdi:recycle",
}

class Source:
    def __init__(self, street_code: int, building_number: int):
        self._street_code: int = street_code
        self._building_number: int = building_number

    def fetch(self):
        args = {
            "streetNum": self._street_code,
            "homeNummber": self._building_number,
        }

        now = datetime.datetime.now()
        args["startMonth"] = now.year
        args["isTreeMonthRange"] = "true"
        args["isYear"] = "false"

        # get json file
        r = requests.get(API_URL, params=args)

        data = json.loads(r.text)

        entries = []  # List that holds collection schedule
        for key, value in data.items():
            month_year: str = key.split("-")
            month: int = int(month_year[0]) + 1
            year: int = int(month_year[1])
        
            for dayValue, wastes in value.items():
                day: int = int(dayValue)
                for waste in wastes:
                    print(waste) # blau / pink / grau
                    entries.append(
                        Collection(
                            date = datetime.date(year, month, day),  # Collection date
                            t = waste,  # Collection type
                            icon = ICON_MAP.get(waste),  # Collection icon
                        )
                    )

        return entries