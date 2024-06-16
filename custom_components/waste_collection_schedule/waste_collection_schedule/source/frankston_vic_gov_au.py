import requests
from datetime import datetime, timedelta
import time
from waste_collection_schedule import Collection

TITLE = "Frankston City Council" # Title will show up in README.md and info.md
DESCRIPTION = "Source script for frankston.vic.gov.au"  # Describe your source
URL = "https://frankston.gov.au"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "45r Wedge Rd": {"address": "45r Wedge Rd, Carrum Downs Vic"},  # Monday
    "300 Wedge Rd": {"address": "300 Wedge Rd, Skye Vic"},  # Monday, but inverse recycling week to 45r Wedge Rd
    "66 Skye Rd": {"address": "66 Skye Rd, Skye Vic"}, #Tuesday
    "160 North Rd": {"address": "160 North Road, Langwarrin Vic"}, #Wednesday
    "65 Golf Links Rd": {"address": "65 Golf Links Rd, Frankston Vic"}, #Thursday
    "107 Nepean Highway": {"address": "107 Nepean Highway, Seaford Vic"} #Friday

}

API_URL = "https://www.frankston.vic.gov.au/My-Property/Waste-and-recycling/My-bins/Bin-collections"
ICON_MAP = {
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
        today = datetime.now().date()
        start_date = datetime.strptime(start_date, "%Y%m%d").date()
        
        # Calculate days until the next collection day
        days_until_next_collection = (collection_day - today.weekday() + 7) % 7
        next_collect = today + timedelta(days=days_until_next_collection)
        
        # Calculate the number of days from the start date to the next collection day
        days_from_start = (next_collect - start_date).days
        
        # Adjust the next collection day if not aligned with the collection cycle
        if days_from_start % (weeks * 7) != 0:
            days_until_aligned = (weeks * 7) - (days_from_start % (weeks * 7))
            next_collect += timedelta(days=days_until_aligned)
        
        next_dates = [next_collect]
        
        # Generate the subsequent collection dates
        for i in range(1, 4 // weeks):
            next_collect += timedelta(days=weeks * 7)
            next_dates.append(next_collect)
        
        return next_dates

    #Shapely is not supported in the project, so we need a  function to check whether address coordinates reside in a given zone's polygon
    def is_point_in_polygon(self, point, polygon):
        x, y = point
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def find_zone(self, lat, long, data):
        point = long, lat
        for feature in data:
            geometry = feature["geometry"]
            if geometry["type"] == "Polygon":
                polygon_coords = geometry["coordinates"][0]
                if self.is_point_in_polygon(point, polygon_coords):
                    return feature["properties"]
            elif geometry["type"] == "MultiPolygon":
                for polygon_coords in geometry["coordinates"]:
                    if self.is_point_in_polygon(point, polygon_coords[0]):
                        return feature["properties"]
        return None

    def fetch(self):
        # Get latitude & longitude of address
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
