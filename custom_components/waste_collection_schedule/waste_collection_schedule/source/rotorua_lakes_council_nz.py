import datetime
import requests
from waste_collection_schedule import Collection
from geopy.geocoders import Nominatim
from bs4 import BeautifulSoup

TITLE = "Rotorua Lakes Council"
DESCRIPTION = "Source for Rotorua Lakes Council"
URL = "https://www.rotorualakescouncil.nz"
TEST_CASES = {
    "Test1": {"address": "1061 Haupapa Street"},
    "Test2": {"address": "369 state highway 33"},
    "Test3": {"address": "17 Tihi road"},
    "Test4": {"address": "12a robin st"},
    "Test5": {"address": "25 kaska rd"}
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
        geolocator = Nominatim(user_agent="hacs_waste_collection_schedule")
        location = geolocator.geocode(self._address)
        if not location:
            print("Geolocation failed for address:", self._address)
            return []

        lat, lon = location.latitude, location.longitude
        
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

        #print("API Response:", data)  # Debug print

        entries = []
        for feature in data.get("features", []):
            attributes = feature.get("attributes", {})
            schedule_html = attributes.get("Collection", "")
            
            if not schedule_html:
                print("No schedule HTML found in attributes:", attributes)
                continue

            soup = BeautifulSoup(schedule_html, 'html.parser')
            list_items = soup.find_all('li')

            if not list_items:
                print("No list items found in schedule HTML:", schedule_html)
                continue
            
            for item in list_items:
                # Extract collection type
                collection_type_tag = item.find('b')
                collection_type = collection_type_tag.get_text() if collection_type_tag else "Unknown"
                collection_type = "Rubbish only" if "Rubbish only" in collection_type else "Rubbish and recycling"

                # Extract date after <br/>
                br_tag = item.find('br')
                if br_tag and br_tag.next_sibling:
                    date_str = br_tag.next_sibling.strip()  

                   
                    try:
                        date_time = datetime.datetime.strptime(date_str, "%A %d %b %Y")
                        date = date_time.date() 
                    except ValueError:
                        print(f"Date parsing error for value: {date_str}")
                        continue  # Skip this entry if date parsing fails

                    entries.append(
                        Collection(
                            date=date,
                            t=collection_type,
                            icon=ICON_MAP.get(collection_type),
                        )
                    )

        return entries
