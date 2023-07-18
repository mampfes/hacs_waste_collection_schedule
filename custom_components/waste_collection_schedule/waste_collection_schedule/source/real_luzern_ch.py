import datetime
from waste_collection_schedule import Collection

import requests
from bs4 import BeautifulSoup

TITLE = "Real Luzern"
DESCRIPTION = "Source script for Real Luzern, Switzerland"
URL = "https://www.real-luzern.ch"

TEST_CASES = {
    "Luzern - Heimatweg": {"municipality_id": 13, "street_id": 766},
    "Luzern - Pliatusblick": {"municipality_id": 13, "street_id": 936},
    "Emmen": {"municipality_id": 6}
}

ICON_MAP = {
    "Kehricht": "mdi:trash-can",
    "Grüngut": "mdi:leaf",
    "Papier": "mdi:newspaper-variant-multiple",
    "Karton": "mdi:package-variant",
    "Altmetall": "mdi:clippy",
    # "Altmetall": "mdi:engine",
}

GERMAN_MONTH_STRING_TO_INT = {
    "Januar": 1,
    "Februar": 2,
    "März": 3,
    "April": 4,
    "Mai": 5,
    "Juni": 6,
    "Juli": 7,
    "August": 8,
    "September": 9,
    "Oktober": 10,
    "November": 11,
    "Dezember": 12,
}


API_URL = "https://www.real-luzern.ch/abfall/sammeldienst/abfallkalender/"


class Source:
    def __init__(self, municipality_id, street_id=None):
        self._municipality_id = municipality_id
        self._street_id = street_id

    def fetch(self):
        # make request
        uri = f"{API_URL}?gemId={self._municipality_id}&strId={self._street_id}"
        r = requests.get(uri)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")

        # extract entries
        entries = []
        waste_type_containers = soup.find(
            "div", class_='tab-content').findChildren('div', recursive=False)
        for waste_type_container in waste_type_containers:
            waste_type = waste_type_container.get('id')
            years = [int(y.text) for y in waste_type_container.findChildren("h3", recursive=False)]
            
            dates_per_year = [c.text.replace(". ", ".").split(
            ) for c in waste_type_container.find_all("div", class_='cols')]

            for (year, dates) in zip(years, dates_per_year):
                for (day, month) in [split_german_date(date) for date in dates]:
                    entries.append(
                        Collection(
                            date=datetime.date(year, month, day),
                            t=waste_type,
                            icon=ICON_MAP.get(waste_type),
                        )
                    )

        return entries


def split_german_date(date_string):
    day, month_string = date_string.strip().split(".")
    month = GERMAN_MONTH_STRING_TO_INT[month_string]
    return (int(day), month)
