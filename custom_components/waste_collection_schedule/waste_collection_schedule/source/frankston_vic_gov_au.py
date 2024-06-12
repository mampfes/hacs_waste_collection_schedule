import requests
from datetime import datetime, timedelta
import time
from waste_collection_schedule import Collection

TITLE = "Frankston Council" # Title will show up in README.md and info.md
DESCRIPTION = "Source script for frankston.vic.gov.au"  # Describe your source
URL = "https://frankston.gov.au"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "14 Lorikeet Ct": {"address": "14 Lorikeet Ct, Frankston Vic"}  # Monday #Thursday
}

API_URL = "https://www.frankston.vic.gov.au/My-Property/Waste-and-recycling/My-bins/Bin-collections"
ICON_MAP = {   # Optional: Dict of waste types and suitable mdi icons
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Green Waste": "mdi:leaf",
    "Glass": "mdl:glass-fragile",
}


class Source:
    def __init__(self, address):  # argX correspond to the args dict in the source configuration
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

        # https://www.here.com/docs/bundle/geocoding-and-search-api-v7-api-reference/page/index.html#/paths/~1geocode/get
        params = {
            "at": "-38.14661485072201,145.13564091954078", #center of search context - lat long
            "apiKey": "tI7s4MoReh2jFaRxp481ThdeynUC-5KIAn6xeKdsGxM",
            "q": self._address,
            "qq": "country=AUS;state=VIC",
        }

        url = "https://geocode.search.hereapi.com/v1/geocode"
        r = requests.get(url, params=params)
        r.raise_for_status()

        lat_long = r.json()["items"][0]["position"]
        print(lat_long)

        ### !TODO: UP TO HERE

        # Get waste collection zone by longitude and latitude
        url = "https://services3.arcgis.com/TJxZpUnYIJOvcYwE/arcgis/rest/services/Waste_Collection_Zones/FeatureServer/0/query" #will need replacing with Frankston one
        
        params ={
            "f": "geojson",
            "outFields": "*",
            "returnGeometry": "true",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "geometryType": "esriGeometryPoint",
            "geometry": str(lat_long["Longitude"]) + "," + str(lat_long["Latitude"]),
        }

        r = requests.get(url, params=params)
        r.raise_for_status()

        waste_schedule = r.json()["features"][0]["properties"]

        entries = []
        
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
    


#test - remove before commit
Source("14 Lorikeet Ct, Frankston")