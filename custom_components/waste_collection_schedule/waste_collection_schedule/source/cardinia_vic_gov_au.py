import time
from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection

TITLE = "Cardinia Shire Council"
DESCRIPTION = "Source script for cardinia.vic.gov.au"
URL = "https://www.cardinia.vic.gov.au"
TEST_CASES = {
    "1015 Manks Rd": {"address": "1015 Manks Rd, Dalmore Vic"},  # Monday
    "6-8 Main St": {"address": "6-8 Main St, Nar Nar Goon Vic"},  # Tuesday
    "875 Princes Hwy": {"address": "875 Princes Hwy, Pakenham Vic"}, # Thursday
    "124 Main St": {"address": "124 Main St, Pakenham Vic"},  # Friday
}

API_URL = "https://www.cardinia.vic.gov.au/info/20002/rubbish_and_recycling/385/bin_collection_days_and_putting_your_bins_out/2#section-2-check-your-bin-collection-days-online"
ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Green Waste": "mdi:leaf",
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
        address = self._address.replace(" ", "+")
        url = "https://corp-geo.mapshare.vic.gov.au/arcgis/rest/services/Geocoder/VMAddressEZIAdd/GeocodeServer/findAddressCandidates?SingleLine=" + address + "&magicKey=GST7YMc0AM9UOsKtGTyVGST7YMc0AM9UOsExAi9XOc50YTc2KQWmObktGMytaikZQDoEUDVIU1FF&f=json"

        r = requests.get(url)
        r.raise_for_status()

        lat_long = r.json()["candidates"][0]["location"]

        # Get waste collection zone by longitude and latitude
        url = "https://services3.arcgis.com/TJxZpUnYIJOvcYwE/arcgis/rest/services/Waste_Collection_Zones/FeatureServer/0/query"
        
        params ={
            "f": "geojson",
            "outFields": "*",
            "returnGeometry": "true",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "geometryType": "esriGeometryPoint",
            "geometry": str(lat_long["x"]) + "," + str(lat_long["y"]),
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
