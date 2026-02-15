import csv
import json
from datetime import datetime, timedelta

import requests

from ..collection import Collection

TITLE = "Toronto (ON)"
DESCRIPTION = "Source for Toronto waste collection"
URL = "https://www.toronto.ca"

TEST_CASES = {
    "224 Wallace Ave": {"street_address": "224 Wallace Ave"},
    "324 Weston Rd": {"street_address": "324 Weston Rd"},
}

CSV_URL = "https://www.toronto.ca/ext/swms/collection_calendar.csv"
PROPERTY_LOOKUP_URL = "https://map.toronto.ca/cotgeocoder/rest/geocoder/suggest"
SCHEDULE_LOOKUP_URL = (
    "https://map.toronto.ca/cotgeocoder/rest/geocoder/findAddressCandidates"
)

ICON_MAP = {
    "GreenBin": "mdi:compost",
    "Garbage": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "YardWaste": "mdi:grass",
    "ChristmasTree": "mdi:pine-tree",
}

PICTURE_MAP = {
    "GreenBin": "https://www.toronto.ca/resources/swm_collection_calendar/img/greenbin.png",
    "Garbage": "https://www.toronto.ca/resources/swm_collection_calendar/img/garbagebin.png",
    "Recycling": "https://www.toronto.ca/resources/swm_collection_calendar/img/bluebin.png",
    "YardWaste": "https://www.toronto.ca/resources/swm_collection_calendar/img/yardwaste.png",
}

VALID_WASTE_TYPES = set(ICON_MAP) | set(PICTURE_MAP)


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def get_first_result(self, json_data, key):
        result = json_data.get("result", {})
        rows = result.get("rows", [])

        if not rows:
            return None

        return rows[0].get(key)

    def fetch(self):
        session = requests.Session()
        entries = []

        # lookup the address key for a particular property address
        property_response = session.get(
            PROPERTY_LOOKUP_URL,
            params={
                "f": "json",
                "matchAddress": 1,
                "matchPlaceName": 1,
                "matchPostalCode": 1,
                "addressOnly": 0,
                "retRowLimit": 100,
                "searchString": self._street_address,
            },
            timeout=30,
        )

        property_json = property_response.json()
        property_key = self.get_first_result(property_json, "KEYSTRING")

        if not property_key:
            return entries

        # lookup the schedule key for the above property key
        schedule_response = session.get(
            SCHEDULE_LOOKUP_URL,
            params={
                "keyString": property_key,
                "unit": "%",
                "areaTypeCode1": "RESW",
            },
            timeout=30,
        )

        schedule_cursor = self.get_first_result(
            schedule_response.json(), "AREACURSOR1"
        )

        if not schedule_cursor:
            return entries

        area_name = schedule_cursor["array"][0]["AREA_NAME"]
        # download schedule csv and figure out what column format
        csv_response = session.get(CSV_URL, timeout=30)
        reader = csv.DictReader(csv_response.text.splitlines())

        # normalize fieldnames (strip whitespace)
        reader.fieldnames = [
            name.strip() if name else name
            for name in reader.fieldnames
        ]

        csv_lines = list(reader)

        calendar_key = None
        week_key = None

        for key in csv_lines[0].keys():
            key_l = key.lower()
            if key_l == "calendar":
                calendar_key = key
            elif "week" in key_l and "start" in key_l:
                week_key = key

        if not calendar_key or not week_key:
            return entries

        days_of_week = "MTWRFSX"
        date_format = "%Y-%m-%d"

        for row in csv_lines:
            calendar_value = row.get(calendar_key)
            if not calendar_value or not calendar_value.startswith(area_name):
                continue

            pickup_date = datetime.strptime(row[week_key], date_format)
            start_weekday = pickup_date.weekday()

            for waste_type in VALID_WASTE_TYPES:
                cell = row.get(waste_type)
                if not isinstance(cell, str) or cell not in days_of_week:
                    continue

                waste_day = pickup_date + timedelta(
                    days=days_of_week.index(cell) - start_weekday
                )

                entries.append(
                    Collection(
                        waste_day.date(),
                        waste_type,
                        picture=PICTURE_MAP.get(waste_type),
                        icon=ICON_MAP.get(waste_type),
                    )
                )

        return entries
