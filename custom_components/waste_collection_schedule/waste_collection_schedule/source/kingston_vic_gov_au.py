import datetime
import json
import requests
from typing import List
from waste_collection_schedule import Collection

# Home Assistant storage support
try:
    from homeassistant.helpers.storage import Store
    HAS_STORAGE = True
except ImportError:
    HAS_STORAGE = False

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
    "services": "https://api.whatbinday.com/V3/Device/{}/Services",
}

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
        self._hass = None
        self._store = None

    def _init_storage(self, hass=None):
        """Initialize storage if Home Assistant is available."""
        if HAS_STORAGE and hass:
            self._hass = hass
            self._store = Store(
                hass,
                version=1,
                key="kingston_waste_collection_device_keys",
                private=True,
                atomic_writes=True
            )

    async def _get_stored_device_key(self) -> str:
        """Get stored device key for this location."""
        if not self._store:
            return None

        try:
            stored_data = await self._store.async_load()
            if stored_data and "device_keys" in stored_data:
                location_key = f"{self.street_number}_{self.street_name}_{self.suburb}_{self.post_code}"
                return stored_data["device_keys"].get(location_key)
        except Exception:
            pass

        return None

    async def _save_device_key(self, device_key: str) -> None:
        """Save device key to storage."""
        if not self._store:
            return

        try:
            stored_data = await self._store.async_load() or {}
            if "device_keys" not in stored_data:
                stored_data["device_keys"] = {}

            location_key = f"{self.street_number}_{self.street_name}_{self.suburb}_{self.post_code}"
            stored_data["device_keys"][location_key] = device_key

            await self._store.async_save(stored_data)
        except Exception:
            pass

    def _register_device(self) -> str:
        """Register a device with the API and get a device key."""
        # Check if we already have a device key in memory
        if self._device_key:
            return self._device_key

        # Try to load from storage first (if storage is available)
        if self._store:
            import asyncio
            try:
                # Try to get existing event loop
                loop = asyncio.get_event_loop()
                if not loop.is_running():
                    stored_key = loop.run_until_complete(self._get_stored_device_key())
                    if stored_key:
                        self._device_key = stored_key
                        return self._device_key
            except (RuntimeError, AttributeError):
                # No event loop or other asyncio issues, continue without storage
                pass

        # Register new device if no stored key found
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

        # Try to save to storage (if storage is available)
        if self._store:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if not loop.is_running():
                    loop.run_until_complete(self._save_device_key(self._device_key))
            except (RuntimeError, AttributeError):
                # No event loop or other asyncio issues, continue without storage
                pass

        return self._device_key

    def _build_address_data(self) -> dict:
        """Build address data structure from user input without geocoding."""
        formatted_address = f"{self.street_number} {self.street_name}, {self.suburb} VIC {self.post_code}, Australia"

        # Create address components structure similar to Google's format
        address_components = [
            {
                "long_name": self.street_number,
                "short_name": self.street_number,
                "types": ["street_number"]
            },
            {
                "long_name": self.street_name,
                "short_name": self.street_name,
                "types": ["route"]
            },
            {
                "long_name": self.suburb,
                "short_name": self.suburb,
                "types": ["locality", "political"]
            },
            {
                "long_name": self.post_code,
                "short_name": self.post_code,
                "types": ["postal_code"]
            },
            {
                "long_name": "Victoria",
                "short_name": "VIC",
                "types": ["administrative_area_level_1", "political"]
            },
            {
                "long_name": "Australia",
                "short_name": "AU",
                "types": ["country", "political"]
            }
        ]

        return {
            "address_components": address_components,
            "formatted_address": formatted_address,
            "geometry": {
                "location": {
                    "lat": -37.9759,  # Default Kingston area coordinates
                    "lng": 145.1350
                },
                "location_type": "APPROXIMATE"
            }
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
            # Build address data from user input
            location_data = self._build_address_data()

            # Get collection schedule
            entries = self._get_collection_schedule(location_data)

            return entries

        except requests.RequestException as e:
            raise Exception(f"Network error: {e}")
        except KeyError as e:
            raise Exception(f"Unexpected API response format: {e}")
        except Exception as e:
            raise Exception(f"Error fetching collection schedule: {e}")
