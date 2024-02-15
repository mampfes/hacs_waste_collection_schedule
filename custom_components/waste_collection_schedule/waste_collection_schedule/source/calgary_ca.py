import json
import logging
from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection

TITLE = "Calgary (AB)"
DESCRIPTION = "Source for Calgary waste collection"
URL = "https://www.calgary.ca"

# ADDRESSES MUST BE ALL CAPS and INCLUDE A QUADRANT
TEST_CASES = {"42 AUBURN SHORES WY SE": {"street_address": "42 AUBURN SHORES WY SE"}}

SCHEDULE_LOOKUP_URL = "https://data.calgary.ca/resource/jq4t-b745.json"

ICON_MAP = {
    "Green": "mdi:leaf",
    "Black": "mdi:trash-can",
    "Blue": "mdi:recycle",
}

WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, street_address):
        self._street_address = street_address.upper()

    def daterange(self, start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)

    def collect(self, single_date, collection_day, interval):
        # check the collection day against the day of the week
        if WEEKDAYS[single_date.weekday()] == collection_day:
            # check the interval (even, odd or every)
            if interval == "EVERY":
                return True

            # get the week number of the current date
            week = single_date.isocalendar()[1]
            week_modulus = week % 2

            # return true if the week moduls corresponds to the collection interval
            if (interval == "EVEN") and (week_modulus == 0):
                return True
            elif (interval == "ODD") and (week_modulus == 1):
                return True
        return False

    def fetch(self):
        LOGGER.warning(
            "looks like calgary moved to recollect and not all collections are visible using this source anymore. https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/ics/recollect.md"
        )
        # lookup the schedule key for the address
        schedule_download = requests.get(
            SCHEDULE_LOOKUP_URL,
            params={"address": self._street_address},
        )
        schedule = json.loads(schedule_download.content.decode("utf-8"))
        entries = []

        for entry in schedule:
            date_format = "%Y-%m-%dT%H:%M:%S.%fZ"

            current_date = datetime.now()
            commodity = entry["commodity"]
            summer_start = datetime.strptime(entry["summer_start"], date_format)
            summer_end = datetime.strptime(entry["summer_end"], date_format)
            winter_start = datetime.strptime(entry["winter_start"], date_format)
            winter_end = datetime.strptime(entry["winter_end"], date_format)
            collection_day_summer = entry["collection_day_summer"]
            collection_day_winter = entry["collection_day_winter"]
            clect_int_summer = entry["clect_int_summer"]
            clect_int_winter = entry["clect_int_winter"]

            # iterate over summer schedule and add entry if needed
            for single_date in self.daterange(summer_start, summer_end):
                # don't need to include dates already passed
                if single_date < current_date:
                    continue
                # if the collection interval is satisfied and if the weekday is the same as the collection day then add the entry
                if self.collect(single_date, collection_day_summer, clect_int_summer):
                    icon = ICON_MAP.get(commodity)
                    entries.append(Collection(single_date.date(), commodity, icon=icon))

            for single_date in self.daterange(winter_start, winter_end):
                # don't need to include dates already passed
                if single_date < current_date:
                    continue
                # if the collection interval is satisfied and if the weekday is the same as the collection day then add the entry
                if self.collect(single_date, collection_day_winter, clect_int_winter):
                    icon = ICON_MAP.get(commodity)
                    entries.append(Collection(single_date.date(), commodity, icon=icon))
        return entries
