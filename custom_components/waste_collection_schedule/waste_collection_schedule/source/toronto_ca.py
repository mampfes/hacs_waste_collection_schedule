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

        schedule_json = schedule_response.json()
        schedule_cursor = self.get_first_result(
            schedule_json, "AREACURSOR1"
        )

        if not schedule_cursor:
            return entries

        area_name = schedule_cursor["array"][0]["AREA_NAME"]
        # download schedule csv and figure out what column format
        csv_response = session.get(CSV_URL, timeout=30)
        csv_lines = list(
            csv.reader(csv_response.text.splitlines(), delimiter=",")
        )

        if not csv_lines:
            return entries

        header = csv_lines[0]

        calendar_col = None
        week_col = None
        id_col = None

        for idx, col in enumerate(header):
            col_l = col.lower()
            if col_l == "calendar":
                calendar_col = idx
            elif "week" in col_l and "start" in col_l:
                week_col = idx
            elif col_l in ("_id", "objectid"):
                id_col = idx

        if calendar_col is None or week_col is None:
            return entries

        days_of_week = "MTWRFSX"
        date_format = "%Y-%m-%d"

        for row in csv_lines[1:]:
            if not row[calendar_col].startswith(area_name):
                continue

            pickup_date = datetime.strptime(
                row[week_col], date_format
            )
            start_weekday = pickup_date.weekday()

            for i, cell in enumerate(row):
                if i in (calendar_col, week_col, id_col):
                    continue

                if cell not in days_of_week:
                    continue

                waste_type = header[i]

                if waste_type not in VALID_WASTE_TYPES:
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
