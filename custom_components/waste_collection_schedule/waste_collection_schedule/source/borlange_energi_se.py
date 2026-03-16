import requests
import re
from datetime import date
from datetime import datetime
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentRequired, SourceArgumentNotFound

TITLE = "Borlänge Energi"
DESCRIPTION = "Waste collection schedule for Borlänge, Sweden"
URL = "https://www.borlange-energi.se/appresource/4.534bcbed17430db9cdb1e5c2/12.3a9c9b4b19a7bbdffe85a22/getcontainerdata"
COUNTRY = "se"
TEST_CASES = {"Mats Knuts Väg": {"pickup_address": "Mats Knuts Väg 100"},
              "Rorsmans Väg 7": {"pickup_address": "Rorsmans Väg 7"}}

DEFAULT_ICON = "mdi:trash-can"
MONTHS = {
    "januari": 1,
    "februari": 2,
    "mars": 3,
    "april": 4,
    "maj": 5,
    "juni": 6,
    "juli": 7,
    "augusti": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "december": 12,
}

ICON_MAP = {
    "Matavfall": "mdi:food-apple",
    "Restavfall": "mdi:trash-can",
    "Pappersförpackningar": "mdi:package-variant",
    "Plastförpackningar": "mdi:bottle-soda-outline",
}


def parse_swedish_date(text: str) -> datetime:
    """
    Extract date from Swedish text like:
    'Nästa tömning sker torsdag den 15 januari'
    """
    match = re.search(r"(\d{1,2})\s+([a-zåäö]+)", text.lower())
    if not match:
        raise ValueError(f"Unrecognized date format: {text}")

    day = int(match.group(1))
    month_name = match.group(2)
    month = MONTHS[month_name]

    year = datetime.now().year
    date = datetime(year, month, day)

    # Falls Datum bereits vorbei ist → nächstes Jahr
    if date.date() < datetime.now().date():
        date = datetime(year + 1, month, day)

    return date


class Source:
    def __init__(self, pickup_address: str):
        if not pickup_address:
            raise SourceArgumentRequired(
                "pickup_address",
                "an address is required to fetch the collection schedule",
            )
        self._pickup_address = pickup_address

    def fetch(self):
        params = {"svAjaxReqParam": "ajax",
                  "pickupAddress": self._pickup_address}

        r = requests.get(URL, params=params, timeout=30)
        r.raise_for_status()

        data = r.json()

        if not isinstance(data, list):
            raise ValueError(
                "Unexpected response format from Borlänge Energi (expected a list)"
            )

        if not data:
            raise SourceArgumentNotFound(
                "pickup_address",
                self._pickup_address,
            )

        entries = []

        for item in data:
            date = parse_swedish_date(item["disposalDay"])
            waste_type = item["contentType"]

            entries.append(
                Collection(
                    date=date.date(),
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type, DEFAULT_ICON),
                )
            )

        return entries
