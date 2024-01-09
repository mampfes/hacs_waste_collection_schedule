import time
from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection

from shapely.geometry import shape, Point
import re

# Currently, Montreal does not offer an iCal/Webcal subscription method.
# The GeoJSON file provides sector-specific details.
# The waste collection schedule is then interpreted from English natural language. Not every sector follows the same structure.
# This method is not highly reliable but serves as an acceptable workaround until a better solution is provided by the city.

TITLE = "Montreal"
DESCRIPTION = "Source script for montreal.ca/info-collectes"
URL = "https://montreal.ca/info-collectes"
TEST_CASES = {
    "6280 Chambord": {"address": "6280 rue Chambord"},
    "2358 Monsabre": {"address": "2358 rue Monsabre"},
    "10785 Clark": {"address": "10785 rue Clark"},
}

API_URL = [
    {
        "type": "Waste",
        "url": "https://donnees.montreal.ca/dataset/2df0fa28-7a7b-46c6-912f-93b215bd201e/resource/5f3fb372-64e8-45f2-a406-f1614930305c/download/collecte-des-ordures-menageres.geojson"
    },
    {
        "type": "Recycling",
        "url": "https://donnees.montreal.ca/dataset/2df0fa28-7a7b-46c6-912f-93b215bd201e/resource/d02dac7d-a114-4113-8e52-266001447591/download/collecte-des-matieres-recyclables.geojson"
    },
    {
        "type": "Food",
        "url": "https://donnees.montreal.ca/dataset/2df0fa28-7a7b-46c6-912f-93b215bd201e/resource/61e8c7e6-9bf1-45d9-8ebe-d7c0d50cfdbb/download/collecte-des-residus-alimentaires.geojson"
    },
    {
        "type": "Green",
        "url": "https://donnees.montreal.ca/dataset/2df0fa28-7a7b-46c6-912f-93b215bd201e/resource/d0882022-c74d-4fe2-813d-1aa37f6427c9/download/collecte-des-residus-verts-incluant-feuilles-mortes.geojson"
    },
    {
        "type": "Bulky",
        "url": "https://donnees.montreal.ca/dataset/2df0fa28-7a7b-46c6-912f-93b215bd201e/resource/2345d55a-5325-488c-b4fc-a885fae458e2/download/collecte-des-residus-de-construction-de-renovation-et-de-demolition-crd-et-encombrants.geojson"
    }
]


ICON_MAP = {
    "Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Food Waste": "mdi:leaf",
    "Green Waste": "mdi:food-apple",
    "Bulky Waste": "mdi:sofa",
}


class Source:
    def __init__(self, address):
        self._address = address

    def get_collections(self, collection_day, weeks, start_date):
        collection_day = time.strptime(collection_day, "%A").tm_wday
        days = (collection_day - datetime.now().date().weekday() + 7) % 7
        next_collect = datetime.now().date() + timedelta(days=days)
        days = abs(next_collect-datetime.strptime(start_date, "%Y-%m-%d").date()).days
        if ((days//7)%weeks):
            next_collect = next_collect + timedelta(days=7)
        next_dates = []
        next_dates.append(next_collect)
        for i in range (1, int(4/weeks)):
            next_collect = next_collect + timedelta(days=(weeks*7))
            next_dates.append(next_collect)
        return next_dates

    def get_latitude_longitude_point(self):
        # Get latitude & longitude of address
        url = "https://geocoder.cit.api.here.com/6.2/search.json"

        params = {
            "gen": "9",
            "app_id": "pYZXmzEqjmR2DG66DRIr",
            "app_code": "T-Z-VT6e6I7IXGuqBfF_vQ",
            "country": "CAN",
            "state": "QC",
            "searchtext": self._address,
            "bbox": "45.39,-73.37;45.72,-74.00",
        }

        r = requests.get(url, params=params)
        r.raise_for_status()

        lat_long = r.json()["Response"]["View"][0]["Result"][0]["Location"]["DisplayPosition"]

        # construct point based on lon/lat returned by geocoder
        return Point(lat_long['Longitude'], lat_long['Latitude'])


    def fetch(self):
        point = self.get_latitude_longitude_point()

        entries = []
        for source in API_URL:

            try:
                # Get waste collection zone by longitude and latitude

                r = requests.get(source["url"])
                r.raise_for_status()

                schedule = r.json()

                # check each polygon to see if it contains the point
                for feature in schedule['features']:
                    sector_shape = shape(feature['geometry'])

                    if sector_shape.contains(point):
                        sector_name = feature['properties']['SECTEUR']
                        #print('Found containing sector:', sector_name)

                        schedule_message = feature['properties']['MESSAGE_EN']

                        days = []


                        # HOUSEHOLD WASTE
                        if source["type"] == "Waste":

                            split_waste_schedule_message = schedule_message.split('\n')
                            month_pattern = r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December) 20[0-9][0-9]\b'

                            for months in split_waste_schedule_message:
                                if re.search(month_pattern, months):
                                    split_months = months.split(':')
                                    month_year = split_months[0].split(' ')
                                    month_name = month_year[1]
                                    year = int(month_year[2])

                                    # remove * character
                                    split_months[1] = split_months[1].replace('*', '')

                                    # Splitting the string by ',' and 'and' to extract individual numbers
                                    days = re.split(r', | and ', split_months[1])
                                    # Converting the extracted strings to integers
                                    days = [int(num) for num in days]

                                    for d in days:
                                        datetime_obj = datetime(year, datetime.strptime(month_name, '%B').month, d)
                                        date_obj = datetime_obj.date()
                                        entries.append(
                                            Collection(
                                                date = date_obj,
                                                t = "Rubbish",
                                                icon = ICON_MAP.get("Rubbish"),
                                            )
                                        )


                        # GREEN WATE
                        if source["type"] == "Green":

                            #print(schedule_message)

                            # Dictionary of weekdays in English with their corresponding numbers
                            weekdays = {
                                "Monday": 0,
                                "Tuesday": 1,
                                "Tuesay": 1, # Typo in message "Collections take place on TUESAYS" (instead fo TUESDAYS).
                                "Wednesday": 2,
                                "Thursday": 3,
                                "Friday": 4,
                                "Saturday": 5,
                                "Sunday": 6
                            }

                            # Searching for the weekday in the sentence
                            collection_day = None
                            for day in weekdays:
                                if re.search(day, schedule_message, re.IGNORECASE):
                                    collection_day = weekdays[day]
                                    break  # Stop searching if the day is found

                            months = {
                                "January": 1,
                                "February": 2,
                                "March": 3,
                                "April": 4,
                                "May": 5,
                                "June": 6,
                                "July": 7,
                                "August": 8,
                                "September": 9,
                                "October": 10,
                                "November": 11,
                                "December": 12,
                            }



                            split_green_schedule_message = schedule_message.split('-')

                            for month in months:
                                for line in split_green_schedule_message:
                                    line = line.split('\n')[0]
                                    line = line.split('.')[0]
                                    line = line.replace('*', '')

                                    if re.search(month, line):

                                        if re.search("weekly", line):
                                            for day in range(1, 32):
                                                try:
                                                    date = datetime(2024, months[month], day)
                                                    if date.weekday() == collection_day:  # Tuesday has index 1
                                                        days.append(date.date())
                                                except ValueError:
                                                    pass  # Skip if the day is out of range for the month

                                        else:
                                            # Splitting the string by ',' and 'and' to extract individual numbers
                                            line = line.replace(';', '')

                                            line = line.replace('.', '')

                                            # Constructing the regex pattern using the variable
                                            month_to_remove = r'\b{}\b'.format(re.escape(month))
                                            line = re.sub(month_to_remove, "", line)

                                            line = re.split(r', | and ', line)

                                            line = [l.lstrip().split(' ')[0] for l in line]

                                            # Converting the extracted strings to integers
                                            days_numbers = [int(num) for num in line]

                                            for day in days_numbers:
                                                date = datetime(2024, months[month], day)
                                                days.append(date.date())
                                        break

                            for d in days:
                                entries.append(
                                    Collection(
                                        date = d,
                                        t = source["type"],
                                        icon = ICON_MAP.get(source["type"]),
                                    )
                                )

                        # RECYCLING OR FOOD
                        elif source["type"] == "Recycling" or  source["type"] == "Food":

                            # Dictionary of weekdays in English with their corresponding numbers
                            weekdays = {
                                "Monday": 0,
                                "Tuesday": 1,
                                "Tuesay": 1, # Typo in message "Collections take place on TUESAYS" (instead fo TUESDAYS).
                                "Wednesday": 2,
                                "Thursday": 3,
                                "Friday": 4,
                                "Saturday": 5,
                                "Sunday": 6
                            }


                            # Searching for the weekday in the sentence
                            collection_day = None
                            for day in weekdays:
                                if re.search(day, schedule_message, re.IGNORECASE):
                                    collection_day = weekdays[day]
                                    break  # Stop searching if the day is found

                            # Iterate through each month and day, and handle the "out of range" error
                            for month in range(1, 13):
                                for day in range(1, 32):
                                    try:
                                        date = datetime(2024, month, day)
                                        if date.weekday() == collection_day:  # Tuesday has index 1
                                            days.append(date.date())
                                    except ValueError:
                                        pass  # Skip if the day is out of range for the month

                            for d in days:
                                entries.append(
                                    Collection(
                                        date = d,
                                        t = source["type"],
                                        icon = ICON_MAP.get(source["type"]),
                                    )
                                )


                        else:
                            #source["type"] == "Bulky" not implmented
                            pass

            except:
                # Probably because the natural language format does not match known formats.
                pass




        return entries
