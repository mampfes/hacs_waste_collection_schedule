import datetime
import json

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "AWL Neuss"  # Title will show up in README.md and info.md
DESCRIPTION = (
    "Source for Bürgerportal AWL Neuss waste collection."  # Describe your source
)
URL = "https://buergerportal.awl-neuss.de/"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "Neuss, Theodor-Heuss-Platz 13": {"street_code": 8650, "building_number": 13},
    "Neuss, Niederstrasse 42": {"street_code": 6810, "building_number": 42},
    "Neuss, Bahnhofstrasse 67": {
        "street_name": "Bahnhofstrasse",
        "building_number": 67,
    },
    "Neuss, Bismarckstrasse 52": {
        "street_name": "Bismarckstrasse",
        "building_number": 52,
    },
    "Neuss, Karlsstrasse 1 (5200)": {"street_code": "5200", "building_number": 1},
}

API_URL = "https://buergerportal.awl-neuss.de/api/v1/calendar"
ICON_MAP = {
    "grau": "mdi:trash-can",
    "pink": "mdi:trash-can",
    "braun": "mdi:leaf",
    "blau": "mdi:package-variant",
    "gelb": "mdi:recycle",
}


PARAM_TRANSLATIONS = {
    "de": {
        "building_number": "Hausnummer",
        "street_name": "Straßenname",
        "street_code": "Straßencode",
    }
}


class Source:
    def __init__(
        self,
        building_number: int,
        street_name: str | None = None,
        street_code: int | None = None,
    ):
        self._street_name: str | None = street_name
        self._street_code: int | None = street_code
        self._building_number: int = building_number

        if not self._street_name and not self._street_code:
            raise SourceArgumentExceptionMultiple(
                ["street_name", "street_code"],
                "Please provide either street_name or street_code",
            )

    def fetch(self):
        # get street code if not set with street
        if self._street_code is None:
            t = requests.get(API_URL + "/townarea-streets")
            data_street = json.loads(t.text)

            street_list = []
            for item in data_street:
                if item["strasseBezeichnung"] == self._street_name:
                    street_list.append(item)

            if len(street_list) == 0:
                raise SourceArgumentNotFoundWithSuggestions(
                    "street_name",
                    self._street_name,
                    suggestions=[item["strasseBezeichnung"] for item in data_street],
                )
            self._street_code = street_list[0]["strasseNummer"]

        args = {
            "streetNum": self._street_code,
            "homeNummber": self._building_number,
        }

        now = datetime.datetime.now()
        args["startMonth"] = now.year
        args["isTreeMonthRange"] = "false"
        args["isYear"] = "true"

        # get json file
        r = requests.get(API_URL, params=args)

        data = json.loads(r.text)

        entries = []  # List that holds collection schedule
        for key, value in data.items():
            month_year: list[str] = key.split("-")
            month: int = int(month_year[0]) + 1
            year: int = int(month_year[1])

            for dayValue, wastes in value.items():
                day: int = int(dayValue)
                for waste in wastes:
                    entries.append(
                        Collection(
                            date=datetime.date(year, month, day),  # Collection date
                            t=waste,  # Collection type
                            icon=ICON_MAP.get(waste),  # Collection icon
                        )
                    )

        return entries
