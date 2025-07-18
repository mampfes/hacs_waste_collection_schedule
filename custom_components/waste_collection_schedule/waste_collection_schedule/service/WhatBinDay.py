#!/usr/bin/env python3

import datetime
import requests
from typing import List, Dict, Optional
from ..collection import Collection


class WhatBinDayService:
    """
    Service for WhatBinDay API (whatbinday.com).
    
    This API provides waste collection schedules for multiple councils
    and regions, primarily in Australia.
    """
    
    API_URLS = {
        "register_device": "https://api.whatbinday.com/V3/Device",
        "services": "https://api.whatbinday.com/V3/Device/{}/Services",
    }

    HEADERS = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Linux; Android 11; Pixel 4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
    }

    DEFAULT_ICON_MAP = {
        "WasteBin": "mdi:trash-can",
        "RecycleBin": "mdi:recycle",
        "GreenBin": "mdi:leaf",
    }

    DEFAULT_BIN_NAMES = {
        "WasteBin": "General waste (landfill)",
        "RecycleBin": "Recycling",
        "GreenBin": "Food and garden waste",
    }

    def __init__(self, device_storage_manager, icon_map: Optional[Dict[str, str]] = None, 
                 bin_names: Optional[Dict[str, str]] = None, app_package: str = "com.socketsoftware.whatbinday.binston"):
        """
        Initialize WhatBinDay service.
        
        Args:
            device_storage_manager: Storage manager for device keys (implements get_device_key/save_device_key)
            icon_map: Custom mapping of bin types to icons
            bin_names: Custom mapping of bin types to display names
            app_package: App package name for device registration
        """
        self._storage = device_storage_manager
        self._icon_map = icon_map or self.DEFAULT_ICON_MAP
        self._bin_names = bin_names or self.DEFAULT_BIN_NAMES
        self._app_package = app_package
        self._device_key = None

    def register_device(self) -> str:
        """Register a device with the API and get a device key."""
        # Check if we already have a device key in memory
        if self._device_key:
            return self._device_key

        # Try to load from storage first
        stored_key = self._storage.get_device_key()
        if stored_key:
            self._device_key = stored_key
            return self._device_key

        # Register new device if no stored key found
        device_data = {
            "model": "SM-G973F",
            "manufacturer": "samsung",
            "api": "V3",
            "client": "2.1.8",
            "status": "Full Product",
            "pushID": "",
            "debug": False,
            "points": [],
            "suburbs": [],
            "regions": [],
            "os": "Android",
            "version": "31",
            "source": self._app_package
        }

        response = requests.post(
            self.API_URLS["register_device"],
            headers=self.HEADERS,
            json=device_data,
            timeout=30
        )
        response.raise_for_status()

        data = response.json()
        if not data.get("success"):
            raise Exception(f"Device registration failed: {data.get('info', 'Unknown error')}")

        self._device_key = data["data"]["key"]

        # Save to storage
        self._storage.save_device_key(self._device_key)

        return self._device_key

    def build_address_data(self, street_number: str, street_name: str, suburb: str, 
                          post_code: str, state: str = "VIC", country: str = "Australia",
                          coordinates: Optional[Dict[str, float]] = None) -> Dict:
        """
        Build address data structure from user input.
        
        Args:
            street_number: Street number/unit
            street_name: Street name
            suburb: Suburb/locality
            post_code: Postal code
            state: State (default: VIC)
            country: Country (default: Australia)
            coordinates: Optional lat/lng coordinates
        """
        formatted_address = f"{street_number} {street_name}, {suburb} {state} {post_code}, {country}"

        # Create address components structure similar to Google's format
        address_components = [
            {
                "long_name": str(street_number),
                "short_name": str(street_number),
                "types": ["street_number"]
            },
            {
                "long_name": str(street_name),
                "short_name": str(street_name),
                "types": ["route"]
            },
            {
                "long_name": str(suburb),
                "short_name": str(suburb),
                "types": ["locality", "political"]
            },
            {
                "long_name": str(post_code),
                "short_name": str(post_code),
                "types": ["postal_code"]
            },
            {
                "long_name": state,
                "short_name": state,
                "types": ["administrative_area_level_1", "political"]
            },
            {
                "long_name": country,
                "short_name": "AU" if country == "Australia" else country,
                "types": ["country", "political"]
            }
        ]

        # Use provided coordinates or defaults
        if coordinates is None:
            # Default coordinates for Victoria, Australia
            coordinates = {"lat": -37.9759, "lng": 145.1350}

        return {
            "address_components": address_components,
            "formatted_address": formatted_address,
            "geometry": {
                "location": coordinates,
                "location_type": "APPROXIMATE"
            }
        }

    def get_collection_schedule(self, location_data: Dict) -> List[Collection]:
        """
        Get bin collection schedule for the location.
        
        Args:
            location_data: Address data from build_address_data()
            
        Returns:
            List of Collection objects
        """
        device_key = self.register_device()

        response = requests.post(
            self.API_URLS["services"].format(device_key),
            headers=self.HEADERS,
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
                bin_name = self._bin_names.get(bin_type, bin_type)
                icon = self._icon_map.get(bin_type, "mdi:trash-can")

                entries.append(
                    Collection(
                        date=collection_date,
                        t=bin_name,
                        icon=icon,
                    )
                )

        return entries

    def fetch_collections(self, street_number: str, street_name: str, suburb: str, 
                         post_code: str, state: str = "VIC", country: str = "Australia",
                         coordinates: Optional[Dict[str, float]] = None) -> List[Collection]:
        """
        Fetch waste collection schedule for an address.
        
        Args:
            street_number: Street number/unit
            street_name: Street name
            suburb: Suburb/locality
            post_code: Postal code
            state: State (default: VIC)
            country: Country (default: Australia)
            coordinates: Optional lat/lng coordinates
            
        Returns:
            List of Collection objects
        """
        try:
            # Build address data from user input
            location_data = self.build_address_data(
                street_number, street_name, suburb, post_code, state, country, coordinates
            )

            # Get collection schedule
            entries = self.get_collection_schedule(location_data)

            return entries

        except requests.RequestException as e:
            raise Exception(f"Network error: {e}")
        except KeyError as e:
            raise Exception(f"Unexpected API response format: {e}")
        except Exception as e:
            raise Exception(f"Error fetching collection schedule: {e}")


class DeviceKeyStorageManager:
    """Base class for device key storage management."""
    
    def get_device_key(self) -> Optional[str]:
        """Get stored device key."""
        raise NotImplementedError
    
    def save_device_key(self, device_key: str) -> None:
        """Save device key to storage."""
        raise NotImplementedError


class NoOpDeviceKeyStorageManager(DeviceKeyStorageManager):
    """No-op storage manager that doesn't persist device keys."""
    
    def __init__(self):
        self._memory_key = None
    
    def get_device_key(self) -> Optional[str]:
        """Get device key from memory (not persisted)."""
        return self._memory_key
    
    def save_device_key(self, device_key: str) -> None:
        """Save device key to memory only (not persisted)."""
        self._memory_key = device_key


class LocationBasedDeviceKeyStorageManager(DeviceKeyStorageManager):
    """Device key storage manager that stores keys by location."""
    
    def __init__(self, storage_manager, street_number: str, street_name: str, 
                 suburb: str, post_code: str):
        """
        Initialize location-based storage manager.
        
        Args:
            storage_manager: Underlying storage implementation
            street_number: Street number for location key
            street_name: Street name for location key
            suburb: Suburb for location key
            post_code: Post code for location key
        """
        self._storage = storage_manager
        self._location_key = f"{street_number}_{street_name}_{suburb}_{post_code}"
    
    def get_device_key(self) -> Optional[str]:
        """Get stored device key for this location."""
        return self._storage.get_device_key_for_location(self._location_key)
    
    def save_device_key(self, device_key: str) -> None:
        """Save device key for this location."""
        self._storage.save_device_key_for_location(self._location_key, device_key)