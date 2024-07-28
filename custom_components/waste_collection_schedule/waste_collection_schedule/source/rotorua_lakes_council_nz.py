import datetime
import requests
from geopy.geocoders import Nominatim
from waste_collection_schedule import Collection

TITLE = "Rotorua Council"
DESCRIPTION = "Source script for Rotorua Council waste collection schedules"
URL = "https://www.rotorua.govt.nz"
TEST_CASES = {
    "ExampleTest": {"address": "1061 Haupapa St"}
}

API_URL = "https://gis.rdc.govt.nz/server/rest/services/Core/RdcServices/MapServer/125/query"
ICON_MAP = {
    "Rubbish only": "mdi:trash-can",
    "Rubbish and recycling": "mdi:recycle",
}

class Source:
    def __init__(self, address):
        self._address = address

    def fetch(self):
        # Geocode the address
        geolocator = Nominatim(user_agent="waste_collection_app")
        location = geolocator.geocode(self._address)
        if not location:
            return []

        lat, lon = location.latitude, location.longitude
        
        # Make the API request
        params = {
            "f": "json",
            "geometryType": "esriGeometryPoint",
            "geometry": f"{lon},{lat}",
            "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "OBJECTID,Name,Collection,Day,FN,Label1,Label2",
            "outSR": 4326,
        }
        response = requests.get(API_URL, params=params)
        data = response.json()

        # Extract and format the schedule
        entries = []
        for feature in data.get("features", []):
            attributes = feature.get("attributes", {})
            schedule = attributes.get("Collection", "")
            day = attributes.get("Day", "")
            collection_type = "Rubbish only" if "only" in schedule else "Rubbish and recycling"
            date_str = attributes.get("FN", "")
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            
            entries.append(
                Collection(
                    date=date,
                    t=collection_type,
                    icon=ICON_MAP.get(collection_type),
                )
            )

        return entries
