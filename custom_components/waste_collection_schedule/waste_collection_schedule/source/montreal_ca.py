import time
from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection

from shapely.geometry import shape, Point
import re

TITLE = "Montreal"
DESCRIPTION = "Source script for montreal.ca/info-collectes"
URL = "https://montreal.ca/info-collectes"
TEST_CASES = {
    "Secteur MHM_42-5_B (2358 Monsabre)": {"address": "2358 rue Monsabre"},
}

API_HOUSEHOLD_WASTE_COLLECTION_URL = "https://donnees.montreal.ca/dataset/2df0fa28-7a7b-46c6-912f-93b215bd201e/resource/5f3fb372-64e8-45f2-a406-f1614930305c/download/collecte-des-ordures-menageres.geojson"
API_RECYCLABLE_MATERIAL_COLLECTION_URL = "https://donnees.montreal.ca/dataset/2df0fa28-7a7b-46c6-912f-93b215bd201e/resource/d02dac7d-a114-4113-8e52-266001447591/download/collecte-des-matieres-recyclables.geojson"
API_FOOD_WASTE_COLLECTION_URL = "https://donnees.montreal.ca/dataset/2df0fa28-7a7b-46c6-912f-93b215bd201e/resource/61e8c7e6-9bf1-45d9-8ebe-d7c0d50cfdbb/download/collecte-des-residus-alimentaires.geojson"
API_GREEN_WASTE_COLLECTION_URL = "https://donnees.montreal.ca/dataset/2df0fa28-7a7b-46c6-912f-93b215bd201e/resource/d0882022-c74d-4fe2-813d-1aa37f6427c9/download/collecte-des-residus-verts-incluant-feuilles-mortes.geojson"
API_CRD_COLLECTION_URL = "https://donnees.montreal.ca/dataset/2df0fa28-7a7b-46c6-912f-93b215bd201e/resource/2345d55a-5325-488c-b4fc-a885fae458e2/download/collecte-des-residus-de-construction-de-renovation-et-de-demolition-crd-et-encombrants.geojson"

ICON_MAP = {
    "Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Food Waste": "mdi:leaf",
    "Green Waste": "mdi:leaf",
    "Bulky Waste": "mdi:leaf",
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

    def fetch(self):
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

        # Get waste collection zone by longitude and latitude
        url = API_HOUSEHOLD_WASTE_COLLECTION_URL

        params ={
            # no param required
        }

        r = requests.get(url, params=params)
        r.raise_for_status()

        # https://stackoverflow.com/questions/20776205/point-in-polygon-with-geojson-in-python

        # construct point based on lon/lat returned by geocoder
        point = Point(lat_long['Longitude'], lat_long['Latitude'])

        waste_schedule = r.json()
        entries = []

        # check each polygon to see if it contains the point
        for feature in waste_schedule['features']:
            sector_shape = shape(feature['geometry'])

            if sector_shape.contains(point):
                sector_name = feature['properties']['SECTEUR']
                print('Found containing sector:', sector_name)

                waste_schedule_message = feature['properties']['MESSAGE_EN']

                split_waste_schedule_message = waste_schedule_message.split('\n')
                month_pattern = r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December) 20[0-9][0-9]\b'

                for months in split_waste_schedule_message:
                    if re.search(month_pattern, months):
                        split_months = months.split(':')
                        month_year = split_months[0].split(' ')
                        month = month_year[1]
                        year = month_year[2]
                        print(month)
                        print(year)

                        # remove * character
                        split_months[1] = split_months[1].replace('*', '')

                        # Splitting the string by ',' and 'and' to extract individual numbers
                        days = re.split(r', | and ', split_months[1])
                        # Converting the extracted strings to integers
                        days = [int(num) for num in days]
                        print(days)






        for next_date in self.get_collections(waste_schedule["rub_day"], waste_schedule["rub_weeks"], waste_schedule["rub_start"]):
            entries.append(
                Collection(
                    date = next_date,
                    t = "Rubbish",
                    icon = ICON_MAP.get("Rubbish"),
                )
            )

        for next_date in self.get_collections(waste_schedule["rec_day"], waste_schedule["rec_weeks"], waste_schedule["rec_start"]):
            entries.append(
                Collection(
                    date = next_date,
                    t = "Recycling",
                    icon = ICON_MAP.get("Recycling"),
                )
            )

        for next_date in self.get_collections(waste_schedule["grn_day"], waste_schedule["grn_weeks"], waste_schedule["grn_start"]):
            entries.append(
                Collection(
                    date = next_date,
                    t = "Green Waste",
                    icon = ICON_MAP.get("Green Waste"),
                )
            )

        return entries
