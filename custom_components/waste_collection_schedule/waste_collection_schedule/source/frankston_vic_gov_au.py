import requests
import json
from shapely.geometry import Point, MultiPolygon, Polygon
from datetime import datetime, timedelta
import time
from waste_collection_schedule import Collection

TITLE = "Frankston Council" # Title will show up in README.md and info.md
DESCRIPTION = "Source script for frankston.vic.gov.au"  # Describe your source
URL = "https://frankston.gov.au"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "45r Wedge Rd": {"address": "45r Wedge Rd, Carrum Downs Vic"},  # Monday #TODO: wrong glass = start date on 20231002
    "300 Wedge Rd": {"address": "300 Wedge Rd, Skye Vic"},  # Monday, but inverse recycling week to 45r Wedge Rd
    "66 Skye Rd": {"address": "66 Skye Rd, Skye Vic"}, #Tuesday
    "160 North Rd": {"address": "160 North Road, Langwarrin Vic"}, #Wednesday #TODO: Wrong glass = start date on 20231004
    "65 Golf Links Rd": {"address": "65 Golf Links Rd, Frankston Vic"}, #Thursday
    "107 Nepean Highway": {"address": "107 Nepean Highway, Seaford Vic"} #Friday

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
        days = abs(next_collect-datetime.strptime(start_date, "%Y%m%d").date()).days
        if ((days//7)%weeks):
            next_collect = next_collect + timedelta(days=7)
        next_dates = []
        next_dates.append(next_collect)
        for i in range (1, int(4/weeks)):
            next_collect = next_collect + timedelta(days=(weeks*7))
            next_dates.append(next_collect)
        return next_dates

    def find_zone(self, lat, long, data):
        point = Point(long, lat)
        for feature in data:
            geometry = feature["geometry"]
            if geometry["type"] == "Polygon":
                # Create a Polygon directly from the coordinates
                polygon_coords = geometry["coordinates"]
                polygon = Polygon(polygon_coords[0])  # Coordinates for a Polygon are a list of lists
            elif geometry["type"] == "MultiPolygon":
                # Create a MultiPolygon directly from the coordinates
                polygons = [Polygon(p[0]) for p in geometry["coordinates"]]
                polygon = MultiPolygon(polygons)
            else:
                continue  # In case there are other types of geometries

            if polygon.contains(point):
                return feature["properties"]
        return None

    def fetch(self):
        # Get latitude & longitude of address

        #TODO: rewrite to use API on Frankston site = https://api.geocode.earth/v1/autocomplete?text=14%20lorikeet%20ct&layers=address,street&boundary.gid=whosonfirst:county:102048609&api_key=ge-39bfbedc55be11c0

        url = "https://api.geocode.earth/v1/autocomplete?text="+self._address+"&layers=address,street&boundary.gid=whosonfirst:county:102048609&api_key=ge-39bfbedc55be11c0"

        r = requests.get(url)
        r.raise_for_status()

        long_lat = r.json()["features"][0]["geometry"]["coordinates"]

        zoneUrl = "https://data.gov.au/data/dataset/0af93e4d-4ef7-4d45-855b-364039c52f98/resource/172777d4-b8dc-4579-a268-acf836da4362/download/frankston-city-council-garbage-collection-zones.json"
        z = requests.get(zoneUrl)
        z.raise_for_status()

        zoneJson = z.json()["features"]

        waste_schedule = self.find_zone(long_lat[1],long_lat[0], zoneJson)

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

        for next_date in self.get_collections(waste_schedule["gls_day"], waste_schedule["gls_weeks"], waste_schedule["gls_start"]):
            entries.append(
                Collection(
                    date = next_date,
                    t = "Glass",
                    icon = ICON_MAP.get("Glass"),
                )
            )

        return entries
    


#test - remove before commit
Source("14 Lorikeet Ct, Frankston")