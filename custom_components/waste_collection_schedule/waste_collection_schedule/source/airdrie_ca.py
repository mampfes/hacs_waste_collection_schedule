from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Airdrie (AB)"
DESCRIPTION = "City of Airdrie waste collection"
URL = "https://www.airdrie.ca"
COUNTRY = "ca"

API_URL = "https://www.airdrie.ca/functions/calendar.cfc"
CALENDAR_ID = 10

ICON_MAP = {
    "Garbage collection": Icons.GENERAL_WASTE,
    "Black garbage cart collection": Icons.GENERAL_WASTE,
    "Recycling collection": Icons.RECYCLING,
    "Blue recycling cart collection": Icons.RECYCLING,
    "Organics collection": Icons.ORGANIC,
    "Green organics cart collection": Icons.ORGANIC,
}

CITIES = {
    13: "Airdrie Meadows",
    6: "Bayside",
    124: "Baysprings",
    123: "Bayview",
    20: "Big Springs",
    25: "Canals",
    167: "Chinook Gate",
    168: "Cobblestone Creek",
    7: "Coopers Crossing",
    118: "Downtown",
    14: "Edgewater",
    28: "Fairways",
    8: "Hillcrest",
    15: "Jensen",
    251: "Key Ranch",
    21: "King's Heights",
    169: "Lanark",
    9: "Luxstone",
    22: "Meadowbrook",
    122: "Midtown",
    10: "Morningside",
    16: "Old Town",
    11: "Prairie Springs",
    24: "Ravenswood",
    35: "Reunion",
    17: "Ridgegate",
    26: "Sagewood",
    255: "Sawgrass Park",
    31: "Silver Creek",
    166: "South Point",
    146: "South Windsong",
    247: "Southwinds",
    32: "Stonegate",
    18: "Summerhill",
    33: "Sunridge",
    119: "The Village",
    23: "Thorburn",
    19: "Waterstone",
    244: "Wildflower",
    36: "Williamstown",
    27: "Willowbrook",
    12: "Windsong",
    34: "Woodside",
}

TEST_CASES = {
    "Coopers Crossing": {"community": "Coopers Crossing"},
    "Morningside": {"community": "Morningside"},
    "Bayside": {"community": "Bayside"},
}

CONFIG_FLOW_TYPES = {
    "community": {
        "type": "SELECT",
        "values": list(CITIES.values()),
        "multiple": False,
    }
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Select your community from the dropdown list.",
}

PARAM_DESCRIPTIONS = {
    "en": {"community": "Select your community from the list"},
}

PARAM_TRANSLATIONS = {
    "en": {"community": "Community"},
}


class Source:
    def __init__(self, community: str):
        self._community_id = None
        for num, name in CITIES.items():
            if name == community:
                self._community_id = num
                break
        if self._community_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "community",
                community,
                list(CITIES.values()),
            )

    def fetch(self):
        now = datetime.now()
        date_start = now.strftime("%m/%d/%Y")
        date_end = (now + timedelta(days=365)).strftime("%m/%d/%Y")

        params = {
            "method": "getEvents",
            "calendarID": CALENDAR_ID,
            "dateStart": date_start,
            "dateEnd": date_end,
        }

        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        events = response.json()

        entries = []
        seen = set()

        for event in events:
            cat_ids = event.get("categoryID", "").split(",")
            if str(self._community_id) not in cat_ids:
                continue

            title = event.get("title", "")
            start_str = event.get("start", "")
            if not start_str:
                continue

            try:
                date = datetime.strptime(start_str.split(" ")[0], "%m/%d/%Y").date()
            except (ValueError, IndexError):
                continue

            key = (date.isoformat(), title)
            if key in seen:
                continue
            seen.add(key)

            icon = ICON_MAP.get(title)
            entries.append(Collection(date=date, t=title, icon=icon))

        entries.sort(key=lambda e: (e.date, e.type))
        return entries
