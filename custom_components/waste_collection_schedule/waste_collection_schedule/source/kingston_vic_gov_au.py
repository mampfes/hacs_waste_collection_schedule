import datetime
import json
import requests
from typing import List
from waste_collection_schedule import Collection

TITLE = "City of Kingston"
DESCRIPTION = "Source for City of Kingston (VIC) waste collection."
URL = "https://www.kingston.vic.gov.au"
TEST_CASES = {
    "randomHouse": {
        "street_number": "30C",
        "street_name": "Oakes Avenue",
        "suburb": "CLAYTON SOUTH",
        "post_code": "3169",
    },
    "randomAppartment": {
        "street_number": "1/51",
        "street_name": "Whatley Street",
        "suburb": "CARRUM",
        "post_code": "3197",
    },
    "randomMultiunit": {
        "street_number": "1/1-5",
        "street_name": "Station Street",
        "suburb": "MOORABBIN",
        "post_code": "3189",
    },
}

API_URLS = {
    "register_device": "https://api.whatbinday.com/V3/Device",
    "geocode": "https://maps.googleapis.com/maps/api/geocode/json",
    "services": "https://api.whatbinday.com/V3/Device/{}/Services",
}

# Google Maps API key from the app's configuration
GOOGLE_API_KEY = "AIzaSyCoEcCHjKouUlN-hsbbrEQW4oAGXDA-v_U"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Linux; Android 11; Pixel 4) AppleWebKit/537.36",
}

ICON_MAP = {
    "WasteBin": "mdi:trash-can",
    "RecycleBin": "mdi:recycle",
    "GreenBin": "mdi:leaf",
}

BIN_NAMES = {
    "WasteBin": "General waste (landfill)",
    "RecycleBin": "Recycling",
    "GreenBin": "Food and garden waste",
}

class Source:
    def __init__(self, street_number: str, street_name: str, suburb: str, post_code: str):
        self.street_number = str(street_number)
        self.street_name = str(street_name)
        self.suburb = str(suburb)
        self.post_code = str(post_code)
        self._device_key = None

    def _register_device(self) -> str:
        """Register a device with the API and get a device key."""
        if self._device_key:
            return self._device_key

        device_data = {
            "model": "HACS_WCS",
            "manufacturer": "HomeAssistant",
            "api": "V1",
            "client": "1.0.0",
            "status": "Full Product",
            "pushID": "(null)",
            "debug": False,
            "points": [],
            "suburbs": [],
            "regions": [],
            "os": "Android",
            "version": "30",
            "source": "com.socketsoftware.whatbinday.binston"
        }

        response = requests.post(
            API_URLS["register_device"],
            headers=HEADERS,
            json=device_data,
            timeout=30
        )
        response.raise_for_status()

        data = response.json()
        if not data.get("success"):
            raise Exception(f"Device registration failed: {data.get('info', 'Unknown error')}")

        self._device_key = data["data"]["key"]
        return self._device_key

    def _geocode_address(self) -> dict:
        """Convert address to geocoded data using Google Maps API."""
        address = f"{self.street_number} {self.street_name}, {self.suburb} VIC {self.post_code}, Australia"

        params = {
            "key": GOOGLE_API_KEY,
            "address": address,
            "sensor": "false",
            "components": "country:Australia",
            "bounds": "-38.0918240879,145.0187443885|-37.9138144402,145.1821660193"
        }

        response = requests.get(API_URLS["geocode"], params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        if not data.get("results"):
            raise Exception(f"Address not found: {address}")

        result = data["results"][0]
        return {
            "address_components": result["address_components"],
            "geometry": result["geometry"],
            "formatted_address": result["formatted_address"]
        }

    def _get_collection_schedule(self, location_data: dict) -> List[Collection]:
        """Get bin collection schedule for the location."""
        device_key = self._register_device()

        response = requests.post(
            API_URLS["services"].format(device_key),
            headers=HEADERS,
            json=location_data,
            timeout=30
        )
        response.raise_for_status()

        data = response.json()
        if not data.get("success"):
            raise Exception(f"Service lookup failed: {data.get('info', 'Unknown error')}")

        # Find the CouncilBinModule in the response
        bin_module = None
        for module in data["data"]:
            if module["ModuleName"] == "CouncilBinModule":
                bin_module = module["Response"]
                break

        if not bin_module:
            raise Exception("No bin collection data found for this address")

        entries = []
        collection_events = bin_module.get("CollectionEvents", [])

        for event in collection_events:
            collection_date = datetime.datetime.strptime(event["Date"], "%Y-%m-%d").date()

            # Create an entry for each bin type collected on this date
            for bin_type in event["Items"]:
                bin_name = BIN_NAMES.get(bin_type, bin_type)
                icon = ICON_MAP.get(bin_type, "mdi:trash-can")

                entries.append(
                    Collection(
                        date=collection_date,
                        t=bin_name,
                        icon=icon,
                    )
                )

        return entries

    def fetch(self) -> List[Collection]:
        """Fetch waste collection schedule."""
        try:
            # Get geocoded address data
            location_data = self._geocode_address()

            # Get collection schedule
            entries = self._get_collection_schedule(location_data)

            return entries

        except requests.RequestException as e:
            raise Exception(f"Network error: {e}")
        except KeyError as e:
            raise Exception(f"Unexpected API response format: {e}")
        except Exception as e:
            raise Exception(f"Error fetching collection schedule: {e}")
