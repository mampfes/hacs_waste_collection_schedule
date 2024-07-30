import datetime
import requests
from waste_collection_schedule import Collection
from bs4 import BeautifulSoup
import logging

_LOGGER = logging.getLogger(__name__)

TITLE = "Rotorua Lakes Council"
DESCRIPTION = "Source for Rotorua Lakes Council"
URL = "https://www.rotorualakescouncil.nz"
API_URL = "https://gis.rdc.govt.nz/server/rest/services/Core/RdcServices/MapServer/125/query"
ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
}
HEADERS = {"User-Agent": "waste-collection-schedule"}

TEST_CASES = {
    "Test1": {"address": "1061 Haupapa Street"},
    "Test2": {"address": "369 state highway 33"},
    "Test3": {"address": "17 Tihi road"},
    "Test4": {"address": "12a robin st"},
    "Test5": {"address": "25 kaska rd"}
}

class Source:
    def __init__(self, address):
        self._address = address

    def fetch_coordinates(self):
        params = {
            "format": "json",
            "q": self._address,
        }
        try:
            response = requests.get("https://nominatim.openstreetmap.org/search", params=params, headers=HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
            if not data:
                raise ValueError(f"Geolocation failed for address: {self._address}")
            return float(data[0]['lat']), float(data[0]['lon'])
        except Exception as e:
            raise ValueError(f"Geolocation failed for address: {self._address} with error: {e}")

    def fetch(self):
        lat, lon = self.fetch_coordinates()

        params = {
            "f": "json",
            "geometryType": "esriGeometryPoint",
            "geometry": f"{lon},{lat}",
            "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "OBJECTID,Name,Collection,Day,FN,Label1,Label2",
            "outSR": 4326,
        }
        try:
            response = requests.get(API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise ValueError(f"API request failed: {e}")

        entries = []
        for feature in data.get("features", []):
            attributes = feature.get("attributes", {})
            schedule_html = attributes.get("Collection", "")
            
            if not schedule_html:
                _LOGGER.warning(f"No schedule HTML found in attributes: {attributes}")
                continue

            soup = BeautifulSoup(schedule_html, 'html.parser')
            list_items = soup.find_all('li')

            if not list_items:
                _LOGGER.warning(f"No list items found in schedule HTML: {schedule_html}")
                continue
            
            for item in list_items:
                collection_type_tag = item.find('b')
                collection_type_text = collection_type_tag.get_text() if collection_type_tag else "Unknown"
                collection_type = "Recycling" if "Rubbish and recycling" in collection_type_text else "Rubbish"

                br_tag = item.find('br')
                if br_tag and br_tag.next_sibling:
                    date_str = br_tag.next_sibling.strip()

                    try:
                        date = datetime.datetime.strptime(date_str, "%A %d %b %Y").date()
                    except ValueError:
                        _LOGGER.error(f"Date parsing error for value: {date_str}")
                        continue

                    entries.append(
                        Collection(
                            date=date,
                            t=collection_type,
                            icon=ICON_MAP.get(collection_type, "mdi:alert-circle"),
                        )
                    )

        if not entries:
            raise ValueError(f"No collection entries found for address: {self._address}")

        return entries
